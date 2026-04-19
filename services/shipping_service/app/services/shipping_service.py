import json
import uuid
from datetime import datetime
from services.shipping_service.app.schemas.shipping_schema import ShippingInput, ShippingOutput

class ShippingService:
    EVENTS_DB_PATH = "data/shipping_events.json"

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
        try:
            with open(ShippingService.EVENTS_DB_PATH, "r+") as file:
                events = json.load(file)
                events.append(event)
                file.seek(0)
                json.dump(events, file, indent=4)
        except FileNotFoundError:
            with open(ShippingService.EVENTS_DB_PATH, "w") as file:
                json.dump([event], file, indent=4)
