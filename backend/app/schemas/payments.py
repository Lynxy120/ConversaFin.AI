from pydantic import BaseModel, ConfigDict


class MidtransNotification(BaseModel):
    model_config = ConfigDict(extra="allow")
    order_id: str
    status_code: str
    gross_amount: str
    signature_key: str
    transaction_status: str
    transaction_id: str | None = None
    payment_type: str | None = None
    fraud_status: str | None = None