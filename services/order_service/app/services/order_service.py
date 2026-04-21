import uuid
from datetime import datetime, timezone
from typing import List, Dict
from common.utils.json_store import append_to_json_file

class OrderService:
    JSON_DB_PATH = "data/orders.json"
    EVENTS_DB_PATH = "data/order_events.json"

    @staticmethod
    def create_order(user_id: str, items: List[Dict], total_amount: float) -> Dict:
        order_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "items": items,
            "total_amount": total_amount,
            "order_status": "PENDING",
            "timestamp": timestamp
        }
        append_to_json_file(OrderService.JSON_DB_PATH, order)
        # Publish event
        OrderService.publish_event("order.created", order)
        return order

    @staticmethod
    def publish_event(event_name: str, event_data: dict):
        from common.messaging.producer import publish_message
        from common.messaging.exchanges import declare_exchange
        from common.messaging.constants import PIPELINE_EXCHANGE, EXCHANGE_TYPE
        import json

        declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)

        event = {
            "event": event_name,
            "data": event_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        publish_message(exchange=PIPELINE_EXCHANGE, routing_key=event_name, message=json.dumps(event))