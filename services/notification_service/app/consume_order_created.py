"""
Consumer for notification_service: listens to order.created events from RabbitMQ and triggers notification sending.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from services.notification_service.app.services.notification_service import NotificationService

EXCHANGE_NAME = "order.events"
QUEUE_NAME = "notification.queue"

def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Notification] Received event:", event)
    event_type = event.get("event")
    if event_type in [
        "order.created",
        "payment.success",
        "payment.failed",
        "inventory.reserved",
        "inventory.failed",
        "order.shipped"
    ]:
        NotificationService.send_notification({
            "order_id": event["data"].get("order_id"),
            "event": event_type
        })

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
    declare_queue(QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[Notification] Waiting for order.created events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()