from pydantic import BaseModel
from typing import List, Dict

class InventoryInput(BaseModel):
    order_id: str
    reserved_items: List[Dict]

class InventoryReserved(BaseModel):
    order_id: str
    reserved_items: List[Dict]
    status: str = "RESERVED"

class InventoryFailed(BaseModel):
    order_id: str
    reason: str
    status: str = "FAILED"
