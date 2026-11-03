import logging
import time
from datetime import datetime, timedelta, timezone
from functools import lru_cache
from typing import Any

from fastapi import BackgroundTasks

from app.core.config import get_settings
from app.repositories import finance as finance_repo
from app.repositories import orders as orders_repo
from app.schemas.payments import MidtransNotification
from app.services import receipt_service as rs
from app.services.midtrans_service import MidtransError, get_midtrans_service, map_status
from app.services.whatsapp_service import get_whatsapp_service, rupiah

log = logging.getLogger("conversafin.pay")
WIB = timezone(timedelta(hours=7))


class PaymentError(Exception): ...


class PaymentService:
    def __init__(self) -> None:
        self._s = get_settings()
        self._mt = get_midtrans_service()

    @staticmethod
    def _res(mid: str, url: str, exp_iso: str | None) -> dict[str, Any]:
        label = datetime.fromisoformat(exp_iso.replace("Z", "+00:00")).astimezone(WIB).strftime("%H:%M WIB") if exp_iso else "-"
        return {"midtrans_order_id": mid, "qr_url": url, "expires_at": exp_iso, "expires_label": label}

    async def create_qris(self, order: dict[str, Any]) -> dict[str, Any]:
        if order["status"] != "pending":
            raise PaymentError(f"order is {order['status']}")
        exp = order.get("payment_expires_at")
        if order.get("midtrans_order_id") and order.get("payment_url") and exp \
                and datetime.fromisoformat(exp.replace("Z", "+00:00")) > datetime.now(timezone.utc) + timedelta(minutes=1):
            return self._res(order["midtrans_order_id"], order["payment_url"], exp)  # reuse valid QR
        items = [{"id": i["sku"], "price": int(float(i["unit_price"])), "quantity": int(i["quantity"]), "name": i["product_name"][:50]}
                 for i in order["order_items"]]
        mid = f"CF-{order['id'].replace('-', '')[:12].upper()}-{int(time.time())}"
        try:
            ch = await self._mt.charge_qris(order_id=mid, items=items, name=order.get("customer_name"), phone=order.get("customer_phone"))
        except MidtransError as e:
            raise PaymentError(str(e)) from e
        await orders_repo.set_payment(order["id"], mid=mid, tx_id=ch["transaction_id"], url=ch["qr_url"], expires=ch["expires_at"])
        return self._res(mid, ch["qr_url"], ch["expires_at"].isoformat() if ch["expires_at"] else None)

    async def handle_notification(self, n: MidtransNotification, bg: BackgroundTasks) -> dict[str, Any]:
        order = await orders_repo.get_by_mid(n.order_id)
        if not order:
            return {"result": "unknown_order"}
        ts, fraud = n.transaction_status, n.fraud_status
        if self._s.midtrans_verify_status:  # re-query Midtrans: never trust the body alone
            try:
                r = await self._mt.get_status(n.order_id)
            except MidtransError as e:
                raise PaymentError(str(e)) from e
            ts, fraud = r.get("transaction_status", ts), r.get("fraud_status")
        new = map_status(ts, fraud)
        if new is None:
            return {"result": "ignored", "transaction_status": ts}
        if new != "paid":
            return {"result": new if await orders_repo.set_status_if_pending(n.order_id, new) else "already_processed"}
        if int(float(n.gross_amount)) != int(float(order["total_price"])):
            log.error("amount mismatch %s", n.order_id)
            return {"result": "amount_mismatch"}
        paid = await orders_repo.mark_paid(n.order_id, n.payment_type)
        if not paid:
            return {"result": "already_processed"}
        bg.add_task(self.post_payment, paid["id"])
        return {"result": "paid", "order_id": paid["id"]}

    async def post_payment(self, order_id: str) -> None:
        wa = get_whatsapp_service()
        o = await orders_repo.get_order(order_id)
        if not o:
            return
        no, to, url = rs.receipt_number(o), o["customer_phone"], ""
        try:
            await finance_repo.record_income(amount=o["total_price"], description=f"Order {no} - {to}", reference_id=o["midtrans_order_id"])
        except Exception:
            log.exception("finance failed %s", order_id)
        try:
            path = await rs.store_receipt(order_id, rs.build_receipt_pdf(o))
            await orders_repo.set_receipt(order_id, path)
            url = await rs.signed_url(path)
        except Exception:
            log.exception("receipt failed %s", order_id)
        try:
            await wa.send_text_message(to, f"Pembayaran {rupiah(o['total_price'])} untuk #{no} berhasil ✅")
            if url:
                await wa.send_document(to, url, f"Receipt-{no}.pdf", "Bukti pembayaran")
            for ow in wa.owner_numbers:
                await wa.send_text_message(ow, f"💰 Masuk: #{no} {rupiah(o['total_price'])} dari {o.get('customer_name') or to}")
        except Exception:
            log.exception("WA notify failed %s", order_id)


@lru_cache
def get_payment_service() -> PaymentService:
    return PaymentService()