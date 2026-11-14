from collections import defaultdict
from datetime import date
from typing import Any

EXPENSE_GROUPS = ("tagihan", "pengeluaran_harian", "hutang")
TYPE_ORDER = {"cash": 0, "bank": 1, "ewallet": 2, "savings": 3}


def _f(v: Any) -> float:
    return float(v or 0)


def _pct(a: float, b: float) -> float | None:
    return round(a / b * 100, 1) if b else None


def enrich_debt(d: dict[str, Any]) -> dict[str, Any]:
    total, paid = _f(d["total_amount"]), _f(d["paid_amount"])
    return {
        **d,
        "total_amount": total,
        "paid_amount": paid,
        "monthly_payment": _f(d.get("monthly_payment")),
        "remaining": max(total - paid, 0.0),
        "pct": min(_pct(paid, total) or 0.0, 100.0),
    }


def _budget_for(b: dict[str, Any], month: str) -> float:
    if b["group_type"] == "tabungan" and b.get("start_date") and b.get("target_date"):
        if not (b["start_date"][:7] <= month <= b["target_date"][:7]):
            return 0.0
    return _f(b["budget_amount"])


def build_dashboard(
    month: str,
    accounts: list[dict],
    bal_flows: list[dict],
    flows: list[dict],
    budgets: list[dict],
    debts: list[dict],
) -> dict[str, Any]:
    amap = {a["id"]: a for a in accounts}
    active = [a for a in accounts if a["is_active"]]
    bal = {a["id"]: _f(a["initial_balance"]) for a in active}
    saved: dict[str, float] = defaultdict(
        float
    )  # net allocation per savings category (non-savings pockets only)
    for r in bal_flows:
        a = amap.get(r["account_id"])
        if not a:
            continue
        v = _f(r["total"])
        if a["id"] in bal:
            bal[a["id"]] += v if r["type"] in ("income", "in") else -v
        if (
            r["group_type"] == "tabungan"
            and a["type"] != "savings"
            and r["type"] in ("out", "in")
        ):
            saved[r["category"]] += v if r["type"] == "out" else -v

    cash = sum(bal[a["id"]] for a in active if a["type"] != "savings")
    savings = sum(bal[a["id"]] for a in active if a["type"] == "savings") + sum(
        saved.values()
    )
    debt_list = [enrich_debt(d) for d in debts]
    debt_left = sum(d["remaining"] for d in debt_list if d["status"] == "active")
    pockets = sorted(
        (
            {
                "id": a["id"],
                "name": a["name"],
                "type": a["type"],
                "balance": bal[a["id"]],
                "is_default": a["is_default"],
            }
            for a in active
        ),
        key=lambda p: (not p["is_default"], TYPE_ORDER[p["type"]], p["name"].lower()),
    )

    act: dict[str, dict[str, float]] = {
        g: defaultdict(float)
        for g in ("pemasukan", "tagihan", "pengeluaran_harian", "hutang", "tabungan")
    }
    for r in flows:
        if r["month"] != month:
            continue
        t, g, c, v = r["type"], r["group_type"], r["category"], _f(r["total"])
        if t == "income" and g == "pemasukan":
            act["pemasukan"][c] += v
        elif t == "expense" and g in EXPENSE_GROUPS:
            act[g][c] += v
        elif g == "tabungan" and not r["is_savings"] and t in ("out", "in"):
            act["tabungan"][c] += v if t == "out" else -v

    bud: dict[str, dict[str, dict]] = {
        g: {} for g in ("pemasukan", "tagihan", "pengeluaran_harian", "tabungan")
    }
    for b in sorted(
        budgets, key=lambda b: b["month"] != "default"
    ):  # month-specific rows override the default template
        bud[b["group_type"]][b["category"]] = b

    def rows(g: str) -> list[dict[str, Any]]:
        cats = set(bud[g]) | {c for c, v in act[g].items() if v}
        out = []
        for c in cats:
            b = bud[g].get(c)
            budget, a = (_budget_for(b, month) if b else 0.0), act[g].get(c, 0.0)
            row: dict[str, Any] = {
                "category": c,
                "budget": budget,
                "actual": a,
                "pct": _pct(a, budget),
            }
            if g == "tabungan":
                tt, sv = (_f(b.get("total_target")) if b else 0.0), max(
                    saved.get(c, 0.0), 0.0
                )
                row |= {
                    "total_target": tt or None,
                    "saved": sv,
                    "goal_pct": _pct(sv, tt),
                    "start_date": b.get("start_date") if b else None,
                    "target_date": b.get("target_date") if b else None,
                }
            out.append(row)
        return sorted(out, key=lambda r: (-r["budget"], -r["actual"], r["category"]))

    groups = {g: rows(g) for g in bud}
    t = lambda g, k: sum(r[k] for r in groups[g])  # noqa: E731
    hutang_b = sum(d["monthly_payment"] for d in debt_list if d["status"] == "active")
    hutang_a = sum(act["hutang"].values())
    pillars = [
        ("pemasukan", "Pemasukan", t("pemasukan", "budget"), t("pemasukan", "actual")),
        ("tabungan", "Tabungan", t("tabungan", "budget"), t("tabungan", "actual")),
        ("tagihan", "Tagihan", t("tagihan", "budget"), t("tagihan", "actual")),
        (
            "pengeluaran",
            "Pengeluaran",
            t("pengeluaran_harian", "budget"),
            t("pengeluaran_harian", "actual"),
        ),
        ("hutang", "Hutang", hutang_b, hutang_a),
    ]
    sisa = {
        k: pillars[0][i] - sum(p[i] for p in pillars[1:])
        for k, i in (("budget", 2), ("actual", 3))
    }
    income, expense = pillars[0][3], pillars[2][3] + pillars[3][3] + hutang_a

    return {
        "month": month,
        "balance": {
            "total": cash + savings,
            "cash": cash,
            "savings": savings,
            "debt_remaining": debt_left,
        },
        "pockets": pockets,
        "summary": [
            {"key": k, "label": lb, "budget": b, "actual": a} for k, lb, b, a in pillars
        ],
        "sisa": sisa,
        "ratio": {"income": income, "expense": expense, "pct": _pct(expense, income)},
        "groups": groups,
        "debts": debt_list,
    }


def build_yearly(
    year: int, flows: list[dict], accounts: list[dict], net_before: float, today: date
) -> dict[str, Any]:
    z = lambda: [0.0] * 12  # noqa: E731
    inc: dict[str, list[float]] = defaultdict(z)
    daily, hutang, tagihan, in_, out_, tab, net = z(), z(), z(), z(), z(), z(), z()
    by_group = {"pengeluaran_harian": daily, "hutang": hutang, "tagihan": tagihan}
    for r in flows:
        m, v, t, g = (
            int(r["month"][5:7]) - 1,
            _f(r["total"]),
            r["type"],
            r["group_type"],
        )
        if t == "income":
            inc[r["category"]][m] += v
        elif t == "expense":
            by_group.get(g, daily)[m] += v
        elif t == "in":
            in_[m] += v
        elif t == "out":
            out_[m] += v
        if g == "tabungan" and not r["is_savings"] and t in ("out", "in"):
            tab[m] += v if t == "out" else -v
        if not r["is_savings"]:
            net[m] += v if t in ("income", "in") else -v

    run = net_before + sum(
        _f(a["initial_balance"])
        for a in accounts
        if a["is_active"] and a["type"] != "savings"
    )
    saldo: list[float | None] = []
    for m in range(12):
        run += net[m]
        saldo.append(None if year == today.year and m + 1 > today.month else run)

    def row(values: list, **kw: Any) -> dict[str, Any]:
        return {**kw, "values": values, "total": sum(values)}

    income_total = [sum(c[m] for c in inc.values()) for m in range(12)]
    expense_total = [daily[m] + hutang[m] + tagihan[m] for m in range(12)]
    known = [s for s in saldo if s is not None]
    return {
        "year": year,
        "income": [
            row(v, category=c)
            for c, v in sorted(inc.items(), key=lambda kv: -sum(kv[1]))
        ],
        "expense": [
            row(daily, key="daily", label="Harian"),
            row(hutang, key="hutang", label="Hutang"),
            row(tagihan, key="tagihan", label="Tagihan"),
        ],
        "summary": [
            row(income_total, key="income", label="Income"),
            row(expense_total, key="expense", label="Expense"),
            row(in_, key="in", label="In"),
            row(out_, key="out", label="Out"),
            row(tab, key="tabungan", label="Tabungan"),
            {
                "key": "saldo",
                "label": "Saldo Cash",
                "values": saldo,
                "total": known[-1] if known else None,
            },
        ],
    }
