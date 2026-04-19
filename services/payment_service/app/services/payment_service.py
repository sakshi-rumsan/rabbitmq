import json
import uuid
from datetime import datetime
from typing import Dict
from services.payment_service.app.schemas.payment_schema import PaymentInput, PaymentSuccess, PaymentFailed

class PaymentService:
    EVENTS_DB_PATH = "data/payment_events.json"

    @staticmethod
    def process_payment(payment_data: Dict) -> Dict:
        payment = PaymentInput(**payment_data)
        # Simulate payment logic (success if amount <= 1000, else fail)
        if payment.total_amount <= 1000:
            transaction_id = str(uuid.uuid4())
            event = PaymentSuccess(
                order_id=payment.order_id,
                transaction_id=transaction_id,
                amount=payment.total_amount
            ).dict()
            PaymentService.publish_event("payment.success", event)
            return event
        else:
            event = PaymentFailed(
                order_id=payment.order_id,
                reason="Insufficient funds",
                status="FAILED"
            ).dict()
            PaymentService.publish_event("payment.failed", event)
            return event

    @staticmethod
    def publish_event(event_name: str, event_data: dict):
        event = {
            "event": event_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            with open(PaymentService.EVENTS_DB_PATH, "r+") as file:
                events = json.load(file)
                events.append(event)
                file.seek(0)
                json.dump(events, file, indent=4)
        except FileNotFoundError:
            with open(PaymentService.EVENTS_DB_PATH, "w") as file:
                json.dump([event], file, indent=4)
        # If event is failed, also publish to DLQ
        if event_name in ["payment.failed", "inventory.failed"]:
            from common.messaging.dlq import publish_to_dlq
            import json as _json
            publish_to_dlq(_json.dumps(event_data))
