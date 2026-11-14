from datetime import date
from typing import Any

from app.core.supabase import get_supabase


# ---- accounts
async def accounts(active_only: bool = True) -> list[dict[str, Any]]:
    c = await get_supabase()
    q = c.table("finance_accounts").select("*")
    if active_only:
        q = q.eq("is_active", True)
    return (await q.order("is_default", desc=True).order("created_at").execute()).data


async def get_account(aid: str) -> dict[str, Any] | None:
    c = await get_supabase()
    r = await c.table("finance_accounts").select("*").eq("id", aid).limit(1).execute()
    return r.data[0] if r.data else None


async def create_account(d: dict[str, Any]) -> dict[str, Any]:
    c = await get_supabase()
    return (await c.table("finance_accounts").insert(d).execute()).data[0]


async def update_account(aid: str, d: dict[str, Any]) -> dict[str, Any] | None:
    c = await get_supabase()
    r = await c.table("finance_accounts").update(d).eq("id", aid).execute()
    return r.data[0] if r.data else None


# ---- budgets
async def budgets(months: list[str]) -> list[dict[str, Any]]:
    c = await get_supabase()
    r = (
        await c.table("finance_budgets")
        .select("*")
        .in_("month", months)
        .order("group_type")
        .order("category")
        .execute()
    )
    return r.data


async def upsert_budget(d: dict[str, Any]) -> dict[str, Any]:
    c = await get_supabase()
    r = (
        await c.table("finance_budgets")
        .upsert(d, on_conflict="month,group_type,category")
        .execute()
    )
    return r.data[0]


async def delete_budget(bid: str) -> bool:
    c = await get_supabase()
    return bool(
        (await c.table("finance_budgets").delete().eq("id", bid).execute()).data
    )


# ---- debts
async def debts() -> list[dict[str, Any]]:
    c = await get_supabase()
    return (
        await c.table("finance_debts")
        .select("*")
        .order("status")
        .order("created_at", desc=True)
        .execute()
    ).data


async def get_debt(did: str) -> dict[str, Any] | None:
    c = await get_supabase()
    r = await c.table("finance_debts").select("*").eq("id", did).limit(1).execute()
    return r.data[0] if r.data else None


async def create_debt(d: dict[str, Any]) -> dict[str, Any]:
    c = await get_supabase()
    return (await c.table("finance_debts").insert(d).execute()).data[0]


async def update_debt(did: str, d: dict[str, Any]) -> dict[str, Any] | None:
    c = await get_supabase()
    r = (
        await c.table("finance_debts")
        .update({**d, "updated_at": "now()"})
        .eq("id", did)
        .execute()
    )
    return r.data[0] if r.data else None


async def delete_debt(did: str) -> bool:
    c = await get_supabase()
    return bool((await c.table("finance_debts").delete().eq("id", did).execute()).data)


async def pay_debt(
    did: str, amount: float, account_id: str | None, on: date, notes: str | None
) -> dict[str, Any]:
    c = await get_supabase()
    r = await c.rpc(
        "finance_pay_debt",
        {
            "p_debt": did,
            "p_amount": amount,
            "p_account": account_id,
            "p_date": on.isoformat(),
            "p_notes": notes,
        },
    ).execute()
    return r.data[0] if isinstance(r.data, list) else r.data


# ---- aggregates
async def flows(frm: date, to: date) -> list[dict[str, Any]]:
    c = await get_supabase()
    return (
        await c.rpc(
            "finance_flows", {"p_from": frm.isoformat(), "p_to": to.isoformat()}
        ).execute()
    ).data


async def balance_flows() -> list[dict[str, Any]]:
    c = await get_supabase()
    return (await c.rpc("finance_balance_flows").execute()).data


async def net_before(d: date) -> float:
    c = await get_supabase()
    return float(
        (await c.rpc("finance_net_before", {"p_before": d.isoformat()}).execute()).data
        or 0
    )


# ---- ledger
async def ledger(
    frm: date | None,
    to: date | None,
    type_: str | None,
    account_id: str | None,
    limit: int,
    offset: int,
) -> tuple[list[dict[str, Any]], int]:
    c = await get_supabase()
    q = c.table("financial_records").select(
        "*, finance_accounts(name,type)", count="exact"
    )
    if frm and to:
        q = q.gte("transaction_date", frm.isoformat()).lte(
            "transaction_date", to.isoformat()
        )
    if type_:
        q = q.eq("type", type_)
    if account_id:
        q = q.eq("account_id", account_id)
    r = (
        await q.order("transaction_date", desc=True)
        .order("created_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )
    return r.data, r.count or 0


async def get_record(rid: str) -> dict[str, Any] | None:
    c = await get_supabase()
    r = (
        await c.table("financial_records")
        .select("id,debt_id")
        .eq("id", rid)
        .limit(1)
        .execute()
    )
    return r.data[0] if r.data else None


async def create_record(d: dict[str, Any]) -> dict[str, Any]:
    c = await get_supabase()
    return (await c.table("financial_records").insert(d).execute()).data[0]


async def delete_record(rid: str) -> bool:
    c = await get_supabase()
    return bool(
        (await c.table("financial_records").delete().eq("id", rid).execute()).data
    )
