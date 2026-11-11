import logging
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from typing import Any, Literal
from uuid import UUID

from app.core.config import get_settings
from app.repositories import finance as repo
from app.schemas.finance import ExtractionResult, Transaction
from app.schemas.webhooks import Message
from app.services.gemini_service import AIError, get_gemini_service
from app.services.media_service import (
    MediaError,
    download_telegram_media,
    validate_media,
)

log = logging.getLogger("conversafin.finance")
WIB = timezone(timedelta(hours=7))
MAX_AMOUNT = 100_000_000_000
Kind = Literal["text", "audio", "image"]
LABEL = {"business": "Bisnis", "personal": "Pribadi"}


class FinanceError(Exception): ...


def idr(v: Any) -> str:
    return "Rp" + f"{int(float(v)):,}".replace(",", ".")


@dataclass
class RunResult:
    extraction: ExtractionResult
    candidates: list[dict[str, Any]] = field(default_factory=list)
    saved: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[str] = field(default_factory=list)


@dataclass
class Outcome:
    action: str
    text: str
    buttons: list[tuple[str, str]] = field(default_factory=list)


class FinanceService:
    def __init__(self) -> None:
        self._s = get_settings()
        self._ai = get_gemini_service()

    # ---------- core pipeline: AI extract -> validate -> classify -> persist ----------
    async def run(
        self,
        *,
        kind: Kind,
        ref: str,
        actor: str,
        source: str,
        save: bool = True,
        text: str | None = None,
        data: bytes | None = None,
        mime: str | None = None,
    ) -> RunResult:
        if kind == "text":
            text = (text or "").strip()[:2000]
            if not text:
                raise FinanceError("Pesan kosong.")
        else:
            mime = validate_media(kind, data or b"", mime)

        today = datetime.now(WIB).date()
        ex = await self._ai.extract(
            kind=kind, today=today, text=text, data=data, mime=mime
        )

        res = RunResult(ex)
        for i, t in enumerate(ex.transactions if ex.is_financial else []):
            reason = self._reject_reason(t)
            if reason:
                res.rejected.append(f"{t.description[:40]} ({reason})")
                continue
            res.candidates.append(
                self._row(t, ex, kind, ref, i, actor, source, today, text)
            )
        if save and res.candidates:
            res.saved = await repo.insert_records(res.candidates)
        return res

    def _reject_reason(self, t: Transaction) -> str | None:
        if not 0 < t.amount <= MAX_AMOUNT:
            return "nominal tidak valid"
        if t.confidence < self._s.finance_min_confidence:
            return "kurang yakin"
        return None

    @staticmethod
    def _row(
        t: Transaction,
        ex: ExtractionResult,
        kind: Kind,
        ref: str,
        i: int,
        actor: str,
        source: str,
        today: date,
        text: str | None,
    ) -> dict[str, Any]:
        try:
            d = date.fromisoformat(t.transaction_date) if t.transaction_date else today
        except ValueError:
            d = today
        return {
            "type": t.type,
            "domain": t.domain,
            "amount": t.amount,
            "category": t.category,
            "description": t.description[:200],
            "merchant": (t.merchant or None) and t.merchant[:120],
            "transaction_date": min(d, today).isoformat(),
            "source": source,
            "input_type": kind,
            "confidence": round(max(0.0, min(1.0, t.confidence)), 2),
            "raw_input": (
                (ex.source_text or (text if kind == "text" else "") or "")[:1000]
            )
            or None,
            "created_by": actor,
            "reference_id": f"{ref}:{i}",
        }

    # ---------- Telegram Adapters ----------
    async def handle_message(self, m: Message) -> Outcome:
        try:
            if m.type == "text":
                res = await self.run(
                    kind="text",
                    text=m.body_text,
                    ref=m.id,
                    actor=m.from_,
                    source="telegram",
                )
            else:
                media = m.audio if m.type == "audio" else m.image
                if not media or not media.id:
                    raise FinanceError("Media tidak valid.")
                data, mime = await download_telegram_media(media.id)
                res = await self.run(kind=m.type, data=data, mime=mime, ref=m.id, actor=m.from_, source="telegram")  # type: ignore[arg-type]
        except (FinanceError, AIError, MediaError) as e:
            return Outcome("fin_error", f"⚠️ {e}")
        except Exception:
            log.exception("finance pipeline failed for %s", m.id)
            return Outcome(
                "fin_error", "⚠️ Terjadi kesalahan sistem. Coba lagi sebentar lagi."
            )
        return self._outcome(res)

    def _outcome(self, r: RunResult) -> Outcome:
        if r.saved:
            lines = [
                f"{'➕' if x['type'] == 'income' else '➖'} {idr(x['amount'])} · {x['category']} · {LABEL[x['domain']]}\n   {x['description']}"
                for x in r.saved
            ]
            txt = f"✅ {len(r.saved)} transaksi tercatat:\n" + "\n".join(lines)
            if r.rejected:
                txt += "\n⚠️ Dilewati: " + "; ".join(r.rejected)
            btn: list[tuple[str, str]] = []
            if len(r.saved) == 1:
                x = r.saved[0]
                other = "personal" if x["domain"] == "business" else "business"
                btn = [
                    (f"fin:dom:{x['id']}", f"Ubah ke {LABEL[other]}"),
                    (f"fin:del:{x['id']}", "Hapus"),
                ]
            return Outcome("fin_saved", txt, btn)
        if r.candidates:
            return Outcome("fin_duplicate", "Transaksi ini sudah pernah dicatat.")
        if r.rejected:
            return Outcome(
                "fin_clarify",
                "Belum cukup jelas: "
                + "; ".join(r.rejected)
                + ". Sebutkan nominal & jenisnya.",
            )
        return Outcome(
            "fin_none",
            r.extraction.clarification or "Tidak ada transaksi keuangan terdeteksi.",
        )

    async def handle_action(self, rid: str) -> Outcome:
        try:
            _, act, raw = rid.split(":", 2)
            rec_id = str(UUID(raw))
        except ValueError:
            return Outcome("fin_error", "Aksi tidak valid.")
        rec = await repo.get_record(rec_id)
        if not rec:
            return Outcome("fin_error", "Catatan tidak ditemukan.")
        if act == "del":
            await repo.delete_record(rec_id)
            return Outcome("fin_deleted", "🗑️ Catatan dihapus.")
        if act == "dom":
            new = "personal" if rec["domain"] == "business" else "business"
            await repo.set_domain(rec_id, new)
            return Outcome(
                "fin_updated",
                f"🔁 Diubah ke {LABEL[new]}: {idr(rec['amount'])} · {rec['description']}",
            )
        return Outcome("fin_error", "Aksi tidak dikenal.")


@lru_cache
def get_finance_service() -> FinanceService:
    return FinanceService()
