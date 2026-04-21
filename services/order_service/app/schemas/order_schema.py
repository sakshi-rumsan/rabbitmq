# Pydantic schemas for Order Service
from pydantic import BaseModel
from typing import List, Dict

class OrderRequest(BaseModel):
    user_id: str
    items: List[Dict]
    total_amount: float

class OrderResponse(BaseModel):
    order_id: str
    user_id: str
    items: List[Dict]
    total_amount: float
    order_status: str
    timestamp: str