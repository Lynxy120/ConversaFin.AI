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