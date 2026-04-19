from pydantic import BaseModel
from typing import Optional

class ShippingInput(BaseModel):
    order_id: str

class ShippingOutput(BaseModel):
    order_id: str
    tracking_id: str
    status: str = "SHIPPED"
