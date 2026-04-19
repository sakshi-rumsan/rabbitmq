from pydantic import BaseModel
from typing import Optional

class NotificationInput(BaseModel):
    event: str
    order_id: str
    user_id: Optional[str] = None

class NotificationSent(BaseModel):
    order_id: str
    event: str
    message: str
    status: str = "SENT"
