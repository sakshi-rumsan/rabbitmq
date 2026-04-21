"""
Consumer for notification_service: listens to all pipeline events from RabbitMQ and triggers notification sending.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from common.messaging.constants import PIPELINE_EXCHANGE, EXCHANGE_TYPE, Q_NOTIFICATION
from services.notification_service.app.services.notification_service import NotificationService


def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Notification] Received event:", event)
    event_type = event.get("event")
    NotificationService.send_notification({
        "order_id": event["data"].get("order_id"),
        "event": event_type
    })

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)
    declare_queue(Q_NOTIFICATION)
    channel.queue_bind(exchange=PIPELINE_EXCHANGE, queue=Q_NOTIFICATION, routing_key="#")
    channel.basic_consume(queue=Q_NOTIFICATION, on_message_callback=callback, auto_ack=True)
    print(f"[Notification] Waiting for order events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
