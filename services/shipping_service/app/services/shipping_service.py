
import json
import uuid
from datetime import datetime
from services.shipping_service.app.schemas.shipping_schema import ShippingInput, ShippingOutput
from common.messaging.connection import get_connection
import pika


class ShippingService:
    EVENTS_DB_PATH = "data/shipping_events.json"
    EXCHANGE_NAME = "order.events"

    @staticmethod
    def create_shipment(shipping_data: dict) -> dict:
        ship = ShippingInput(**shipping_data)
        tracking_id = f"TRK{str(uuid.uuid4())[:8].upper()}"
        event = ShippingOutput(
            order_id=ship.order_id,
            tracking_id=tracking_id
        ).dict()
        ShippingService.publish_event("order.shipped", event)
        return event

    @staticmethod
    def publish_event(event_name: str, event_data: dict):
        event = {
            "event": event_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }

        # 1. Write to local log file for debugging
        try:
            with open(ShippingService.EVENTS_DB_PATH, "r+") as file:
                events = json.load(file)
                events.append(event)
                file.seek(0)
                json.dump(events, file, indent=4)
                file.truncate()
        except FileNotFoundError:
            with open(ShippingService.EVENTS_DB_PATH, "w") as file:
                json.dump([event], file, indent=4)

        # 2. Publish to RabbitMQ so downstream services receive it
        try:
            from common.messaging.constants import PIPELINE_EXCHANGE, EXCHANGE_TYPE
            connection = get_connection()
            channel = connection.channel()
            channel.exchange_declare(
                exchange=PIPELINE_EXCHANGE,
                exchange_type=EXCHANGE_TYPE,
                durable=True
            )
            channel.basic_publish(
                exchange=PIPELINE_EXCHANGE,
                routing_key=event_name,
                body=json.dumps(event),
                properties=pika.BasicProperties(delivery_mode=2)
            )
            connection.close()
        except Exception as e:
            print(f"[ShippingService] Failed to publish event to RabbitMQ: {e}")