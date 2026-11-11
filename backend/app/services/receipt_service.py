from datetime import datetime, timedelta, timezone
from typing import Any

from fpdf import FPDF

from app.core.config import get_settings
from app.core.supabase import get_supabase

WIB = timezone(timedelta(hours=7))
_t = (
    lambda v: str(v if v is not None else "-")
    .encode("latin-1", "replace")
    .decode("latin-1")
)  # noqa: E731
_idr = lambda v: "Rp " + f"{int(float(v)):,}".replace(",", ".")  # noqa: E731


def receipt_number(o: dict[str, Any]) -> str:
    return "CF-" + o["id"].replace("-", "")[:8].upper()


def build_receipt_pdf(o: dict[str, Any]) -> bytes:
    pdf = FPDF(format="A5")
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 9, _t(get_settings().brand), new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 9)
    pdf.cell(
        0,
        5,
        "BUKTI PEMBAYARAN / PAYMENT RECEIPT",
        new_x="LMARGIN",
        new_y="NEXT",
        align="C",
    )
    pdf.ln(5)
    paid = (
        datetime.fromisoformat(o["paid_at"].replace("Z", "+00:00"))
        .astimezone(WIB)
        .strftime("%d %b %Y %H:%M WIB")
        if o.get("paid_at")
        else "-"
    )
    for k, v in (
        ("No. Receipt", receipt_number(o)),
        ("Tanggal Bayar", paid),
        ("Pelanggan", o.get("customer_name") or "-"),
        ("ID Telegram", o.get("customer_phone")),
        ("Metode", (o.get("payment_type") or "qris").upper()),
        ("Ref. Midtrans", o.get("midtrans_order_id")),
        ("Status", "LUNAS / PAID"),
    ):
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(38, 5.5, k)
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(0, 5.5, _t(v), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(230, 240, 238)
    for w, h, a in (
        (58, "Produk", "L"),
        (12, "Qty", "C"),
        (29, "Harga", "R"),
        (29, "Subtotal", "R"),
    ):
        pdf.cell(w, 7, h, border=1, align=a, fill=True)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    for i in o.get("order_items", []):
        pdf.cell(58, 6.5, _t(i["product_name"])[:32], border=1)
        pdf.cell(12, 6.5, str(i["quantity"]), border=1, align="C")
        pdf.cell(29, 6.5, _idr(i["unit_price"]), border=1, align="R")
        pdf.cell(29, 6.5, _idr(i["subtotal"]), border=1, align="R")
        pdf.ln()
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(99, 8, "TOTAL", border=1, align="R")
    pdf.cell(29, 8, _idr(o["total_price"]), border=1, align="R")
    pdf.ln(12)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(
        0, 5, "Terima kasih. Dokumen dibuat otomatis oleh ConversaFin.AI", align="C"
    )
    return bytes(pdf.output())


async def store_receipt(order_id: str, pdf: bytes) -> str:
    path = f"{order_id}.pdf"
    await (await get_supabase()).storage.from_(get_settings().receipt_bucket).upload(
        path, pdf, {"content-type": "application/pdf", "upsert": "true"}
    )
    return path


async def signed_url(path: str) -> str:
    s = get_settings()
    r = (
        await (await get_supabase())
        .storage.from_(s.receipt_bucket)
        .create_signed_url(path, s.receipt_url_ttl)
    )
    u = r.get("signedURL") or r.get("signedUrl") or ""
    return u if u.startswith("http") else f"{s.supabase_url.rstrip('/')}/storage/v1{u}"
