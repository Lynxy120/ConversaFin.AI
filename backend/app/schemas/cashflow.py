import math
from datetime import date as Date
from typing import Annotated, Literal, Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

Group = Literal["pemasukan", "tagihan", "pengeluaran_harian", "tabungan", "hutang"]
BudgetGroup = Literal["pemasukan", "tagihan", "pengeluaran_harian", "tabungan"]
MONTH_RE = r"^\d{4}-(0[1-9]|1[0-2])$"
Money = Annotated[float, Field(ge=0, le=1e13)]
Positive = Annotated[float, Field(gt=0, le=1e13)]


class AccountIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    type: Literal["cash", "bank", "ewallet", "savings"]
    initial_balance: float = Field(0, ge=-1e13, le=1e13)


class AccountPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=40)
    type: Literal["cash", "bank", "ewallet", "savings"] | None = None
    initial_balance: float | None = Field(None, ge=-1e13, le=1e13)
    is_active: bool | None = None


class BudgetIn(BaseModel):
    month: str = Field("default", pattern=r"^(default|\d{4}-(0[1-9]|1[0-2]))$")
    group_type: BudgetGroup
    category: str = Field(min_length=1, max_length=60)
    budget_amount: Money = 0
    total_target: Money | None = None
    start_date: Date | None = None
    target_date: Date | None = None

    @model_validator(mode="after")
    def _plan(self) -> Self:
        self.category = self.category.strip().lower()
        if not self.category:
            raise ValueError("Category is required")
        if self.group_type == "tabungan":
            if not (self.total_target and self.start_date and self.target_date):
                raise ValueError(
                    "Savings plan needs total target, start date and target date"
                )
            if self.target_date < self.start_date:
                raise ValueError("Target date is before start date")
            n = max(
                1,
                (self.target_date.year - self.start_date.year) * 12
                + self.target_date.month
                - self.start_date.month
                + 1,
            )
            self.budget_amount = math.ceil(self.total_target / n)
        else:
            self.total_target = self.start_date = self.target_date = None
        return self


class DebtIn(BaseModel):
    category: str = Field(min_length=1, max_length=40)
    description: str | None = Field(None, max_length=200)
    total_amount: Positive
    paid_amount: Money = 0
    monthly_payment: Money = 0

    @model_validator(mode="after")
    def _ok(self) -> Self:
        if self.paid_amount > self.total_amount:
            raise ValueError("Paid amount exceeds total")
        return self


class DebtPatch(BaseModel):
    category: str | None = Field(None, min_length=1, max_length=40)
    description: str | None = Field(None, max_length=200)
    total_amount: Positive | None = None
    paid_amount: Money | None = None
    monthly_payment: Money | None = None


class DebtPay(BaseModel):
    amount: Positive
    account_id: UUID | None = None
    date: Date | None = None
    notes: str | None = Field(None, max_length=300)


class TxIn(BaseModel):
    type: Literal["income", "expense", "in", "out"]
    date: Date
    account_id: UUID | None = None
    group_type: Group | None = None
    category: str = Field(min_length=1, max_length=60)
    description: str | None = Field(None, max_length=200)
    amount: Positive
    notes: str | None = Field(None, max_length=300)
    domain: Literal["business", "personal"] = "personal"

    @model_validator(mode="after")
    def _group(self) -> Self:
        if self.type == "income":
            self.group_type = "pemasukan"
        elif self.type == "expense":
            self.group_type = self.group_type or "pengeluaran_harian"
            if self.group_type not in ("tagihan", "pengeluaran_harian", "hutang"):
                raise ValueError(
                    "Expense must be tagihan, pengeluaran_harian or hutang"
                )
        elif self.group_type not in (None, "tabungan"):
            raise ValueError("Transfers can only be grouped as tabungan")
        return self
