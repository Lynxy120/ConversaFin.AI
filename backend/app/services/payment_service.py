import logging
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

import httpx
from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.core.format import rupiah
from app.integrations.telegram import get_telegram_client
from app.repositories import finance as finance_repo
from app.repositories import orders as orders_repo
from app.schemas.payments import MidtransNotification
from app.services import receipt_service as rs
from app.services.midtrans_service import (
    MidtransError,
    get_midtrans_service,
    map_status,
)

log = logging.getLogger("conversafin.pay")
WIB = timezone(timedelta(hours=7))


class PaymentError(Exception): ...


class PaymentService:
    def __init__(self) -> None:
        self._s, self._mt, self._tg = (
            get_settings(),
            get_midtrans_service(),
            get_telegram_client(),
        )

    @staticmethod
    def _res(mid: str, url: str, exp_iso: str | None) -> dict[str, Any]:
        label = (
            datetime.fromisoformat(exp_iso.replace("Z", "+00:00"))
            .astimezone(WIB)
            .strftime("%H:%M WIB")
            if exp_iso
            else "-"
        )
        return {
            "midtrans_order_id": mid,
            "qr_url": url,
            "expires_at": exp_iso,
            "expires_label": label,
        }

    async def create_qris(self, order: dict[str, Any]) -> dict[str, Any]:
        if order["status"] != "pending":
            raise PaymentError(f"order is {order['status']}")
        exp = order.get("payment_expires_at")
        if (
            order.get("midtrans_order_id")
            and order.get("payment_url")
            and exp
            and datetime.fromisoformat(exp.replace("Z", "+00:00"))
            > datetime.now(timezone.utc) + timedelta(minutes=1)
        ):
            return self._res(
                order["midtrans_order_id"], order["payment_url"], exp
            )  # reuse valid QR: no double charge
        items = [
            {
                "id": i["sku"],
                "price": int(float(i["unit_price"])),
                "quantity": int(i["quantity"]),
                "name": i["product_name"][:50],
            }
            for i in order["order_items"]
        ]
        mid = f"CF-{order['id'].replace('-', '')[:12].upper()}-{int(time.time())}"
        try:
            ch = await self._mt.charge_qris(
                order_id=mid, items=items, name=order.get("customer_name"), phone=None
            )
        except MidtransError as e:
            raise PaymentError(str(e)) from e
        await orders_repo.set_payment(
            order["id"],
            mid=mid,
            tx_id=ch["transaction_id"],
            url=ch["qr_url"],
            expires=ch["expires_at"],
        )
        return self._res(
            mid,
            ch["qr_url"],
            ch["expires_at"].isoformat() if ch["expires_at"] else None,
        )

    async def send_qris(self, chat_id: int, order: dict[str, Any]) -> dict[str, Any]:
        try:
            pay = await self.create_qris(order)
        except PaymentError as e:
            log.error("QRIS failed %s: %s", order["id"], e)
            return await self._tg.send_message(
                chat_id, "⚠️ QRIS belum dapat dibuat. Tim kami akan menghubungi Anda."
            )
        cap = f"Scan QRIS untuk membayar {rupiah(order['total_price'])}.\nBerlaku hingga {pay['expires_label']}."
        png = None
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as c:
                r = await c.get(pay["qr_url"])
            if r.status_code == 200 and r.headers.get("content-type", "").startswith(
                "image/"
            ):
                png = r.content
        except httpx.HTTPError:
            log.warning("QR download failed for %s", order["id"])
        res = await self._tg.send_photo(chat_id, png, cap) if png else {"ok": False}
        return (
            res
            if res["ok"]
            else await self._tg.send_message(chat_id, f"{cap}\n{pay['qr_url']}")
        )

    async def handle_notification(
        self, n: MidtransNotification, bg: BackgroundTasks
    ) -> dict[str, Any]:
        order = await orders_repo.get_by_mid(n.order_id)
        if not order:
            return {"result": "unknown_order"}
        ts, fraud = n.transaction_status, n.fraud_status
        if (
            self._s.midtrans_verify_status
        ):  # re-query Midtrans: never trust the body alone
            try:
                r = await self._mt.get_status(n.order_id)
            except MidtransError as e:
                raise PaymentError(str(e)) from e
            ts, fraud = r.get("transaction_status", ts), r.get("fraud_status")
        new = map_status(ts, fraud)
        if new is None:
            return {"result": "ignored", "transaction_status": ts}
        if new != "paid":
            return {
                "result": (
                    new
                    if await orders_repo.set_status_if_pending(n.order_id, new)
                    else "already_processed"
                )
            }
        if int(float(n.gross_amount)) != int(float(order["total_price"])):
            log.error("amount mismatch %s", n.order_id)
            return {"result": "amount_mismatch"}
        paid = await orders_repo.mark_paid(n.order_id, n.payment_type)
        if not paid:
            return {"result": "already_processed"}
        bg.add_task(self.post_payment, paid["id"])
        return {"result": "paid", "order_id": paid["id"]}

    async def post_payment(self, order_id: str) -> None:
        o = await orders_repo.get_order(order_id)
        if not o:
            return
        no, chat, tg = rs.receipt_number(o), int(o["chat_id"]), self._tg
        try:
            await finance_repo.record_income(
                amount=o["total_price"],
                description=f"Order {no} - {o.get('customer_name') or chat}",
                reference_id=o["midtrans_order_id"],
            )
        except Exception:
            log.exception("finance insert failed %s", order_id)
        pdf = None
        try:
            pdf = rs.build_receipt_pdf(o)
            await orders_repo.set_receipt(
                order_id, await rs.store_receipt(order_id, pdf)
            )
        except Exception:
            log.exception("receipt failed %s", order_id)
        await tg.send_message(
            chat,
            f"✅ Pembayaran {rupiah(o['total_price'])} untuk #{no} diterima. Terima kasih!",
        )
        if pdf:
            await tg.send_document(
                chat, pdf, f"Receipt-{no}.pdf", "🧾 Bukti pembayaran"
            )
        for owner in self._s.owner_ids:
            await tg.send_message(
                owner,
                f"💰 Masuk: #{no} {rupiah(o['total_price'])} dari {o.get('customer_name') or chat}",
            )


@lru_cache
def get_payment_service() -> PaymentService:
    return PaymentService()
