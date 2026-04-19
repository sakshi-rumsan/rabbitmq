from pydantic import BaseModel
from typing import Optional

class PaymentInput(BaseModel):
    order_id: str
    total_amount: float
    user_id: str

class PaymentSuccess(BaseModel):
    order_id: str
    transaction_id: str
    amount: float
    status: str = "SUCCESS"

class PaymentFailed(BaseModel):
    order_id: str
    reason: str
    status: str = "FAILED"
