from typing import Literal, get_args

from pydantic import BaseModel

# No defaults on purpose: this model doubles as the Gemini response_schema.
Category = Literal[
    "sales", "other_income", "inventory", "operations", "payroll", "marketing", "shipping", "tax",
    "utilities", "rent", "food", "transport", "shopping", "health", "entertainment", "education",
    "family", "debt", "other",
]
CATEGORIES: tuple[str, ...] = get_args(Category)


class Transaction(BaseModel):
    type: Literal["income", "expense"]
    domain: Literal["business", "personal"]
    amount: int
    category: Category
    description: str
    merchant: str | None
    transaction_date: str | None
    confidence: float


class ExtractionResult(BaseModel):
    source_text: str | None
    is_financial: bool
    transactions: list[Transaction]
    clarification: str | None