import asyncio
from datetime import date, datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from postgrest.exceptions import APIError

from app.core.security import require_admin
from app.repositories import cashflow as repo
from app.schemas.cashflow import (
    MONTH_RE,
    AccountIn,
    AccountPatch,
    BudgetIn,
    DebtIn,
    DebtPatch,
    DebtPay,
    TxIn,
)
from app.services.cashflow_service import build_dashboard, build_yearly, enrich_debt

router = APIRouter(
    prefix="/finance", tags=["cashflow"], dependencies=[Depends(require_admin)]
)
WIB = timezone(timedelta(hours=7))


def _today() -> date:
    return datetime.now(WIB).date()


def _bounds(m: str) -> tuple[date, date]:
    y, mo = int(m[:4]), int(m[5:7])
    return date(y, mo, 1), date(y + (mo == 12), mo % 12 + 1, 1) - timedelta(days=1)


async def _run(coro: Any) -> Any:
    try:
        return await coro
    except APIError as e:
        code = str(getattr(e, "code", "") or "")
        status, msg = {
            "23505": (409, "Already exists"),
            "23503": (422, "Related record not found"),
            "P0002": (404, "Not found"),
            "22023": (422, "Amount exceeds the remaining debt"),
        }.get(code, (500, "Database error"))
        raise HTTPException(status, msg) from e


# ---------- aggregates
@router.get("/dashboard")
async def dashboard(month: str | None = Query(None, pattern=MONTH_RE)):
    m = month or _today().strftime("%Y-%m")
    frm, to = _bounds(m)
    accts, bal, flows, buds, debts = await asyncio.gather(
        repo.accounts(False),
        repo.balance_flows(),
        repo.flows(frm, to),
        repo.budgets(["default", m]),
        repo.debts(),
    )
    return build_dashboard(m, accts, bal, flows, buds, debts)


@router.get("/yearly")
async def yearly(year: int | None = Query(None, ge=2000, le=2100)):
    y = year or _today().year
    accts, flows, before = await asyncio.gather(
        repo.accounts(True),
        repo.flows(date(y, 1, 1), date(y, 12, 31)),
        repo.net_before(date(y, 1, 1)),
    )
    return build_yearly(y, flows, accts, before, _today())


# ---------- accounts
@router.get("/accounts")
async def list_accounts(include_inactive: bool = False):
    return await repo.accounts(not include_inactive)


@router.post("/accounts", status_code=201)
async def create_account(b: AccountIn):
    return await _run(repo.create_account(b.model_dump()))


@router.patch("/accounts/{aid}")
async def patch_account(aid: UUID, b: AccountPatch):
    cur = await repo.get_account(str(aid))
    if not cur:
        raise HTTPException(404, "Account not found")
    d = b.model_dump(exclude_unset=True)
    if not d:
        raise HTTPException(400, "No fields to update")
    if cur["is_default"] and d.get("is_active") is False:
        raise HTTPException(409, "The default account cannot be deactivated")
    return await _run(repo.update_account(str(aid), d))


# ---------- budgets (setup)
@router.get("/budgets")
async def list_budgets(
    month: str = Query("default", pattern=r"^(default|\d{4}-(0[1-9]|1[0-2]))$")
):
    return await repo.budgets([month])


@router.put("/budgets")
async def put_budget(b: BudgetIn):
    d = b.model_dump(mode="json")
    return await _run(repo.upsert_budget(d))


@router.delete("/budgets/{bid}")
async def delete_budget(bid: UUID):
    if not await repo.delete_budget(str(bid)):
        raise HTTPException(404, "Budget not found")
    return {"status": "deleted"}


# ---------- debts
@router.get("/debts")
async def list_debts():
    return [enrich_debt(d) for d in await repo.debts()]


@router.post("/debts", status_code=201)
async def create_debt(b: DebtIn):
    d = b.model_dump()
    d["category"] = d["category"].strip()
    d["status"] = "paid" if d["paid_amount"] >= d["total_amount"] else "active"
    return enrich_debt(await _run(repo.create_debt(d)))


@router.patch("/debts/{did}")
async def patch_debt(did: UUID, b: DebtPatch):
    cur = await repo.get_debt(str(did))
    if not cur:
        raise HTTPException(404, "Debt not found")
    d = b.model_dump(exclude_unset=True)
    if not d:
        raise HTTPException(400, "No fields to update")
    total, paid = d.get("total_amount", float(cur["total_amount"])), d.get(
        "paid_amount", float(cur["paid_amount"])
    )
    if paid > total:
        raise HTTPException(422, "Paid amount exceeds total")
    d["status"] = "paid" if paid >= total else "active"
    return enrich_debt(await _run(repo.update_debt(str(did), d)))


@router.post("/debts/{did}/pay")
async def pay_debt(did: UUID, b: DebtPay):
    row = await _run(
        repo.pay_debt(
            str(did),
            b.amount,
            str(b.account_id) if b.account_id else None,
            b.date or _today(),
            b.notes,
        )
    )
    return enrich_debt(row)


@router.delete("/debts/{did}")
async def delete_debt(did: UUID):
    if not await repo.delete_debt(str(did)):
        raise HTTPException(404, "Debt not found")
    return {"status": "deleted"}


# ---------- ledger (REKAPAN TRANSAKSI)
@router.get("/ledger")
async def ledger(
    month: str | None = Query(None, pattern=MONTH_RE),
    type_: Literal["income", "expense", "in", "out"] | None = Query(None, alias="type"),
    account_id: UUID | None = None,
    limit: int = Query(15, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    frm, to = _bounds(month) if month else (None, None)
    items, total = await repo.ledger(
        frm, to, type_, str(account_id) if account_id else None, limit, offset
    )
    return {"items": items, "total": total}


@router.post("/ledger", status_code=201)
async def add_record(b: TxIn):
    row: dict[str, Any] = {
        "type": b.type,
        "domain": b.domain,
        "amount": b.amount,
        "category": b.category.strip().lower(),
        "description": b.description,
        "notes": b.notes,
        "group_type": b.group_type,
        "transaction_date": b.date.isoformat(),
        "source": "web",
    }
    if b.account_id:
        row["account_id"] = str(b.account_id)
    return await _run(repo.create_record(row))


@router.delete("/ledger/{rid}")
async def delete_record(rid: UUID):
    r = await repo.get_record(str(rid))
    if not r:
        raise HTTPException(404, "Record not found")
    if r["debt_id"]:
        raise HTTPException(409, "Debt payments cannot be deleted here")
    await repo.delete_record(str(rid))
    return {"status": "deleted"}
