from typing import Any

from postgrest.exceptions import APIError

from app.core.supabase import get_supabase


async def record_income(*, amount: Any, description: str, reference_id: str) -> bool:
    try:
        await (await get_supabase()).table("financial_records").insert({
            "type": "income", "domain": "business", "amount": float(amount), "category": "sales",
            "description": description, "source": "midtrans", "reference_id": reference_id,
        }).execute()
        return True
    except APIError as e:
        if "23505" in str(e):
            return False
        raise

async def insert_records(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Idempotent batch insert. Returns ONLY newly inserted rows ([] = all duplicates)."""
    r = await (await get_supabase()).table("financial_records").upsert(
        rows, on_conflict="source,reference_id", ignore_duplicates=True).execute()
    return r.data


async def get_record(rec_id: str) -> dict[str, Any] | None:
    r = await (await get_supabase()).table("financial_records").select("*").eq("id", rec_id).limit(1).execute()
    return r.data[0] if r.data else None


async def set_domain(rec_id: str, domain: str) -> None:
    await (await get_supabase()).table("financial_records").update({"domain": domain}).eq("id", rec_id).execute()


async def delete_record(rec_id: str) -> None:
    await (await get_supabase()).table("financial_records").delete().eq("id", rec_id).execute()