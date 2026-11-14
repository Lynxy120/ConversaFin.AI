from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from itertools import combinations
from typing import Any

WIB = timezone(timedelta(hours=7))
WEEKDAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
SEV = {"high": 0, "medium": 1, "low": 2, "positive": 3}


def _f(v: Any) -> float:
    return float(v or 0)


def _pct(cur: float, prev: float) -> float | None:
    return round((cur - prev) / prev * 100, 1) if prev else None


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))


def idr(v: float) -> str:
    return "Rp" + f"{int(round(v)):,}".replace(",", ".")


def _local(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(WIB)


def build_insights(
    *,
    frm: date,
    to: date,
    paid: list[dict],
    prev_paid: list[dict],
    statuses: list[dict],
    records: list[dict],
    products: list[dict],
) -> dict[str, Any]:
    days = (to - frm).days + 1
    revenue, prev_rev = sum(_f(o["total_price"]) for o in paid), sum(
        _f(o["total_price"]) for o in prev_paid
    )
    n, prev_n = len(paid), len(prev_paid)
    aov, prev_aov = (revenue / n if n else 0.0), (prev_rev / prev_n if prev_n else 0.0)

    # ---- products ----
    agg: dict[str, dict[str, Any]] = {}
    for o in paid:
        for i in o["order_items"]:
            a = agg.setdefault(
                i["sku"],
                {
                    "sku": i["sku"],
                    "name": i["product_name"],
                    "units": 0,
                    "revenue": 0.0,
                },
            )
            a["units"] += int(i["quantity"])
            a["revenue"] += _f(i["subtotal"])
    prev_units: Counter[str] = Counter()
    for o in prev_paid:
        for i in o["order_items"]:
            prev_units[i["sku"]] += int(i["quantity"])
    ranked = sorted(agg.values(), key=lambda a: -a["revenue"])
    best = [
        {
            "sku": a["sku"],
            "name": a["name"],
            "units": a["units"],
            "revenue": round(a["revenue"]),
            "share": round(a["revenue"] / revenue * 100, 1) if revenue else 0.0,
            "prev_units": prev_units[a["sku"]],
            "trend": _pct(a["units"], prev_units[a["sku"]]),
        }
        for a in ranked[:5]
    ]
    slow = [
        {"sku": p["sku"], "name": p["name"]} for p in products if p["sku"] not in agg
    ][:8]

    # ---- customers ----
    cust: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"name": None, "orders": 0, "spend": 0.0}
    )
    for o in paid:
        c = cust[o["chat_id"]]
        c["name"] = o.get("customer_name") or c["name"] or "Customer"
        c["orders"] += 1
        c["spend"] += _f(o["total_price"])
    prev_ids = {o["chat_id"] for o in prev_paid}
    returning = {k for k, v in cust.items() if v["orders"] >= 2 or k in prev_ids}
    unique = len(cust)
    repeat_rate = round(len(returning) / unique * 100, 1) if unique else 0.0
    ret_rev = sum(cust[k]["spend"] for k in returning)

    hours, wdays = [0] * 24, [0] * 7
    for o in paid:
        if o.get("paid_at"):
            t = _local(o["paid_at"])
            hours[t.hour] += 1
            wdays[t.weekday()] += 1
    peak_hour = max(range(24), key=hours.__getitem__) if any(hours) else None
    peak_day = WEEKDAYS[max(range(7), key=wdays.__getitem__)] if any(wdays) else None

    single: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()
    items_total = 0
    for o in paid:
        skus = sorted({i["sku"] for i in o["order_items"]})
        items_total += sum(int(i["quantity"]) for i in o["order_items"])
        single.update(skus)
        pairs.update(combinations(skus, 2))
    bundles = []
    for (a, b), cnt in pairs.most_common(3):
        if cnt < 2:
            continue
        pa, pb = (
            agg[a]["revenue"] / agg[a]["units"],
            agg[b]["revenue"] / agg[b]["units"],
        )
        bundles.append(
            {
                "a": agg[a]["name"],
                "b": agg[b]["name"],
                "count": cnt,
                "lift": round(cnt * n / (single[a] * single[b]), 2),
                "bundle_price": round((pa + pb) * 0.9 / 500) * 500,
            }
        )
    top = [
        {"name": v["name"], "orders": v["orders"], "spend": round(v["spend"])}
        for v in sorted(cust.values(), key=lambda v: -v["spend"])[:5]
    ]

    # ---- money ----
    biz = [r for r in records if r["domain"] == "business"]
    income = sum(_f(r["amount"]) for r in biz if r["type"] == "income") or revenue
    biz_exp = sum(_f(r["amount"]) for r in biz if r["type"] == "expense")
    pers_exp = sum(
        _f(r["amount"])
        for r in records
        if r["type"] == "expense" and r["domain"] == "personal"
    )
    cats: Counter[str] = Counter()
    for r in biz:
        if r["type"] == "expense":
            cats[r.get("category") or "other"] += _f(r["amount"])
    top_cat, top_cat_amt = cats.most_common(1)[0] if cats else (None, 0.0)
    margin = round((income - biz_exp) / income * 100, 1) if income else None

    cnt = Counter(o["status"] for o in statuses)
    terminal = sum(cnt[s] for s in ("paid", "pending", "expired", "failed"))
    conv = cnt["paid"] / terminal if terminal else None
    expiry = cnt["expired"] / terminal if terminal else None
    pend_amt = sum(_f(o["total_price"]) for o in statuses if o["status"] == "pending")
    exp_amt = sum(_f(o["total_price"]) for o in statuses if o["status"] == "expired")

    rev_delta = _pct(revenue, prev_rev)

    # ---- health score ----
    parts = [
        (
            "margin",
            "Margin",
            margin,
            0.30,
            0.5 if margin is None else _clamp(margin / 30),
        ),
        (
            "growth",
            "Growth",
            rev_delta,
            0.25,
            0.5 if rev_delta is None else _clamp((rev_delta + 20) / 40),
        ),
        ("loyalty", "Loyalty", repeat_rate, 0.25, _clamp(repeat_rate / 40)),
        (
            "conversion",
            "Payments",
            None if conv is None else round(conv * 100, 1),
            0.20,
            0.5 if conv is None else _clamp(conv / 0.85),
        ),
    ]
    score = round(sum(w * s for _, _, _, w, s in parts) * 100)
    label = (
        "Strong"
        if score >= 75
        else (
            "Healthy"
            if score >= 55
            else "Needs attention" if score >= 35 else "At risk"
        )
    )

    # ---- recommendations ----
    recs: list[dict[str, Any]] = []

    def add(
        id_: str,
        sev: str,
        cat: str,
        title: str,
        detail: str,
        action: str,
        impact: str | None = None,
    ) -> None:
        recs.append(
            {
                "id": id_,
                "severity": sev,
                "category": cat,
                "title": title,
                "detail": detail,
                "action": action,
                "impact": impact,
            }
        )

    if margin is not None:
        if margin < 15:
            add(
                "margin_low",
                "high",
                "margin",
                f"Margin is thin at {margin:.0f}%",
                f"Business costs took {100 - margin:.0f}% of income."
                + (
                    f" Largest cost: {top_cat} ({idr(top_cat_amt)})." if top_cat else ""
                ),
                "Renegotiate the largest cost, or raise prices by 5% on your top sellers.",
                f"About {idr(revenue * 0.05)} extra profit per period at a 5% price rise",
            )
        elif margin >= 30:
            add(
                "margin_good",
                "positive",
                "margin",
                f"Healthy margin at {margin:.0f}%",
                "Costs are well under control.",
                "Reinvest part of the surplus in your best seller or in promotion.",
            )
    if rev_delta is not None:
        if rev_delta <= -10:
            add(
                "rev_down",
                "high",
                "revenue",
                f"Revenue fell {abs(rev_delta):.0f}% vs the previous period",
                f"{idr(revenue)} now against {idr(prev_rev)} before.",
                (
                    f"Run a 48-hour promo on {best[0]['name']} and message past customers."
                    if best
                    else "Message past customers with an offer."
                ),
                f"Recovering the gap is worth {idr(prev_rev - revenue)}",
            )
        elif rev_delta >= 10:
            add(
                "rev_up",
                "positive",
                "revenue",
                f"Revenue grew {rev_delta:.0f}% vs the previous period",
                f"{idr(revenue)} now against {idr(prev_rev)} before.",
                "Make sure stock and staff cover the higher demand.",
            )
    if best and best[0]["share"] >= 40:
        add(
            "concentration",
            "medium",
            "product",
            f"{best[0]['name']} drives {best[0]['share']:.0f}% of revenue",
            "One product carries the business; a stock-out would hurt.",
            "Keep a stock buffer and build a second hero product through a bundle.",
        )
    for b in best:
        if b["trend"] is not None and b["prev_units"] >= 3 and b["trend"] <= -30:
            add(
                f"decline_{b['sku']}",
                "medium",
                "product",
                f"{b['name']} sales dropped {abs(b['trend']):.0f}%",
                f"{b['units']} units now against {b['prev_units']} before.",
                "Check price and stock, then send a Telegram promo to past buyers.",
            )
        elif b["trend"] is not None and b["units"] >= 3 and b["trend"] >= 30:
            add(
                f"rising_{b['sku']}",
                "positive",
                "product",
                f"{b['name']} is trending up {b['trend']:.0f}%",
                f"{b['units']} units now against {b['prev_units']} before.",
                "Feature it in promotions and keep extra stock.",
            )
    if peak_hour is not None and n >= 5:
        add(
            "peak",
            "low",
            "operations",
            f"Orders peak around {peak_hour:02d}:00"
            + (f", strongest on {peak_day}s" if peak_day else ""),
            f"{hours[peak_hour]} paid orders landed in that hour.",
            f"Prepare stock and broadcast the menu at {max(peak_hour - 1, 0):02d}:30.",
        )
    if expiry is not None and terminal >= 5 and expiry >= 0.25:
        add(
            "expiry",
            "high" if expiry >= 0.4 else "medium",
            "cash",
            f"{expiry * 100:.0f}% of QRIS orders expired unpaid",
            f"{idr(exp_amt)} in orders never completed.",
            "Send a reminder 5 minutes before expiry and raise the QRIS expiry to 30 minutes.",
            f"Up to {idr(exp_amt)} recoverable",
        )
    if cnt["pending"] >= 3:
        add(
            "pending",
            "medium",
            "cash",
            f"{idr(pend_amt)} waiting for payment",
            f"{cnt['pending']} orders are still unpaid.",
            "Follow up on the Orders page before the QRIS codes expire.",
            f"{idr(pend_amt)} at stake",
        )
    if unique >= 5:
        if repeat_rate < 30:
            add(
                "loyalty_low",
                "medium",
                "customer",
                f"Only {repeat_rate:.0f}% of customers came back",
                "Most buyers purchase once.",
                "Offer a 10% voucher on the second purchase, sent 3 days after the first.",
            )
        elif repeat_rate >= 50:
            add(
                "loyalty_good",
                "positive",
                "customer",
                f"{repeat_rate:.0f}% of customers are repeat buyers",
                f"They bring {idr(ret_rev)} of revenue.",
                "Start a small loyalty perk for your top customers.",
            )
    if bundles and bundles[0]["lift"] >= 1.2:
        b = bundles[0]
        add(
            "bundle",
            "low",
            "product",
            f"{b['a']} + {b['b']} are bought together",
            f"{b['count']} orders contain both ({b['lift']}x more often than chance).",
            f"Offer them as a bundle at {idr(b['bundle_price'])} (10% off).",
        )
    if slow:
        add(
            "slow",
            "low",
            "product",
            f"{len(slow)} active products had no sales",
            ", ".join(s["name"] for s in slow[:4]) + ("…" if len(slow) > 4 else ""),
            "Discount, bundle, or deactivate them to keep the catalog focused.",
        )
    if pers_exp + biz_exp > 0 and pers_exp / (pers_exp + biz_exp) >= 0.35:
        add(
            "personal",
            "medium",
            "margin",
            f"{pers_exp / (pers_exp + biz_exp) * 100:.0f}% of recorded spending is personal",
            f"{idr(pers_exp)} personal against {idr(biz_exp)} business.",
            "Set a fixed personal withdrawal so shop cash stays predictable.",
        )
    if (
        top_cat
        and biz_exp
        and top_cat_amt / biz_exp >= 0.5
        and (margin is None or margin >= 15)
    ):
        add(
            "cost_focus",
            "low",
            "margin",
            f"{top_cat.replace('_', ' ').title()} is {top_cat_amt / biz_exp * 100:.0f}% of business costs",
            f"{idr(top_cat_amt)} this period.",
            "Compare two more suppliers before the next purchase.",
        )
    recs.sort(key=lambda r: SEV[r["severity"]])

    return {
        "has_data": n > 0 or bool(records),
        "from": frm.isoformat(),
        "to": to.isoformat(),
        "days": days,
        "health": {
            "score": score,
            "label": label,
            "parts": [
                {"key": k, "label": lb, "value": v, "score": round(s * 100)}
                for k, lb, v, _, s in parts
            ],
        },
        "kpis": {
            "revenue": round(revenue),
            "revenue_delta": rev_delta,
            "orders": n,
            "orders_delta": _pct(n, prev_n),
            "aov": round(aov),
            "aov_delta": _pct(aov, prev_aov),
            "income": round(income),
            "expense": round(biz_exp),
            "profit": round(income - biz_exp),
            "margin": margin,
            "conversion_rate": None if conv is None else round(conv * 100, 1),
            "expiry_rate": None if expiry is None else round(expiry * 100, 1),
            "pending_amount": round(pend_amt),
            "pending_count": cnt["pending"],
        },
        "best_sellers": best,
        "slow_movers": slow,
        "customers": {
            "unique": unique,
            "returning": len(returning),
            "repeat_rate": repeat_rate,
            "returning_revenue": round(ret_rev),
            "new_revenue": round(revenue - ret_rev),
            "hours": hours,
            "weekdays": wdays,
            "peak_hour": peak_hour,
            "peak_day": peak_day,
            "avg_items": round(items_total / n, 1) if n else 0.0,
            "bundles": bundles,
            "top": top,
        },
        "recommendations": recs[:8],
    }
