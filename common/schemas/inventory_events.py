# Pydantic schemas for Inventory Events
from pydantic import BaseModel

class InventoryReservedEvent(BaseModel):
    product_id: int
    quantity: int

class InventoryDepletedEvent(BaseModel):
    product_id: int
    message: str