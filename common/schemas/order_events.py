# Pydantic schemas for Order Events
from pydantic import BaseModel

class OrderCreatedEvent(BaseModel):
    order_id: int
    item_name: str
    quantity: int

class OrderCancelledEvent(BaseModel):
    order_id: int
    reason: str