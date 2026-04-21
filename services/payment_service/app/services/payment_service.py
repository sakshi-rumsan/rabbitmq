import json
import uuid
from datetime import datetime, timezone
from typing import Dict
from services.payment_service.app.schemas.payment_schema import PaymentInput, PaymentSuccess, PaymentFailed
from common.messaging.connection import get_connection
from common.utils.json_store import append_to_json_file
import pika


class PaymentService:
    EVENTS_DB_PATH = "data/payment_events.json"
    EXCHANGE_NAME = "order.events"

    @staticmethod
    def process_payment(payment_data: Dict) -> Dict:
        payment = PaymentInput(**payment_data)
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
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        append_to_json_file(PaymentService.EVENTS_DB_PATH, event)

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
            print(f"[PaymentService] Failed to publish event to RabbitMQ: {e}")

        # 3. Route failures to DLQ
        if event_name == "payment.failed":
            from common.messaging.dlq import publish_to_dlq
            publish_to_dlq(json.dumps(event))