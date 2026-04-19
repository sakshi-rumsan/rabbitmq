import json
import uuid
from datetime import datetime
from typing import List, Dict

class OrderService:
    JSON_DB_PATH = "data/orders.json"
    EVENTS_DB_PATH = "data/order_events.json"

    @staticmethod
    def create_order(user_id: str, items: List[Dict], total_amount: float) -> Dict:
        order_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        order = {
            "order_id": order_id,
            "user_id": user_id,
            "items": items,
            "total_amount": total_amount,
            "order_status": "PENDING",
            "timestamp": timestamp
        }
        # Save order to JSON DB
        try:
            with open(OrderService.JSON_DB_PATH, "r+") as file:
                data = json.load(file)
                data.append(order)
                file.seek(0)
                json.dump(data, file, indent=4)
        except FileNotFoundError:
            with open(OrderService.JSON_DB_PATH, "w") as file:
                json.dump([order], file, indent=4)
        # Publish event
        OrderService.publish_event("order.created", order)
        return order

    @staticmethod
    def publish_event(event_name: str, event_data: dict):
        # Publish event to RabbitMQ exchange (fanout for pub/sub)
        from common.messaging.producer import publish_message
        from common.messaging.exchanges import declare_exchange
        import json

        exchange_name = "order.events"
        # Ensure the exchange exists (fanout type for pub/sub)
        declare_exchange(exchange_name, exchange_type="fanout")

        event = {
            "event": event_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        message = json.dumps(event)
        # In fanout, routing_key is ignored, but must be provided
        publish_message(exchange=exchange_name, routing_key="", message=message)