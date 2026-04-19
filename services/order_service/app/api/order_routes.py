from services.order_service.app.services.order_service import OrderService
from services.order_service.app.schemas.order_schema import OrderRequest, OrderResponse

def create_order_service(order_data: dict) -> dict:
    """
    Accepts order data, validates, creates order in JSON, and publishes event to a JSON file. Returns order dict.
    """
    order_req = OrderRequest(**order_data)
    order = OrderService.create_order(
        user_id=order_req.user_id,
        items=order_req.items,
        total_amount=order_req.total_amount
    )
    return OrderResponse(**order).dict()

