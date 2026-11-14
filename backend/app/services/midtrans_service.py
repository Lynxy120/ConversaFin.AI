import hashlib
import hmac
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import httpx

from app.core.config import get_settings

WIB = timezone(timedelta(hours=7))


class MidtransError(Exception): ...


def map_status(ts: str, fraud: str | None = None) -> str | None:
    if ts == "settlement" or (ts == "capture" and fraud in (None, "accept")):
        return "paid"
    return {
        "expire": "expired",
        "cancel": "cancelled",
        "deny": "failed",
        "failure": "failed",
    }.get(ts)


class MidtransService:
    def __init__(self) -> None:
        self._s = get_settings()
        self._base = (
            "https://api.midtrans.com"
            if self._s.midtrans_is_production
            else "https://api.sandbox.midtrans.com"
        )

    async def _call(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        ok: tuple[int, ...] = (200, 201),
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self._base,
                timeout=20,
                auth=httpx.BasicAuth(self._s.midtrans_server_key, ""),
                headers={"Accept": "application/json"},
            ) as c:
                r = await c.request(method, path, json=payload)
            d = r.json()
        except (httpx.HTTPError, ValueError) as e:
            raise MidtransError(repr(e)) from e
        if int(d.get("status_code", r.status_code)) not in ok:
            raise MidtransError(
                f"{d.get('status_code')}: {d.get('status_message')} {d.get('validation_messages', '')}"
            )
        return d

    async def charge_qris(
        self,
        *,
        order_id: str,
        items: list[dict[str, Any]],
        name: str | None,
        phone: str | None,
    ) -> dict[str, Any]:
        gross = sum(i["price"] * i["quantity"] for i in items)
        d = await self._call(
            "POST",
            "/v2/charge",
            {
                "payment_type": "qris",
                "transaction_details": {"order_id": order_id, "gross_amount": gross},
                "item_details": items,
                "customer_details": {
                    "first_name": (name or "Customer")[:100],
                    "phone": phone or "",
                },
                "qris": {"acquirer": "gopay"},
                "custom_expiry": {
                    "expiry_duration": self._s.midtrans_qris_expiry_minutes,
                    "unit": "minute",
                },
            },
        )
        qr = next(
            (
                a["url"]
                for a in d.get("actions", [])
                if a.get("name") == "generate-qr-code"
            ),
            f"{self._base}/v2/qris/{d['transaction_id']}/qr-code",
        )
        exp = (
            datetime.strptime(d["expiry_time"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=WIB)
            if d.get("expiry_time")
            else None
        )
        return {
            "transaction_id": d.get("transaction_id"),
            "qr_url": qr,
            "expires_at": exp,
        }

    async def get_status(self, order_id: str) -> dict[str, Any]:
        return await self._call("GET", f"/v2/{order_id}/status", ok=(200, 201, 407))

    def verify_signature(
        self, order_id: str, status_code: str, gross: str, sig: str
    ) -> bool:
        raw = f"{order_id}{status_code}{gross}{self._s.midtrans_server_key}".encode()
        return hmac.compare_digest(hashlib.sha512(raw).hexdigest(), sig or "")

    async def cancel(self, order_id: str) -> dict[str, Any]:
        return await self._call("POST", f"/v2/{order_id}/cancel", ok=(200, 201))


@lru_cache
def get_midtrans_service() -> MidtransService:
    return MidtransService()
