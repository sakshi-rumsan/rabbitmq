# Pydantic schemas for Payment Events
from pydantic import BaseModel

class PaymentProcessedEvent(BaseModel):
    payment_id: int
    order_id: int
    status: str

class PaymentFailedEvent(BaseModel):
    payment_id: int
    order_id: int
    error_message: str