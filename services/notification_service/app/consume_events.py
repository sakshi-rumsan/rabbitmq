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
    try:
        event = json.loads(body)
        print("[Notification] Received event:", event)
        order_id = event["data"].get("order_id")
        if not order_id:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        NotificationService.send_notification({
            "order_id": order_id,
            "event": event["event"]
        })
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[Notification] Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

def main():
    connection = get_connection()
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)
    declare_queue(Q_NOTIFICATION)
    channel.queue_bind(exchange=PIPELINE_EXCHANGE, queue=Q_NOTIFICATION, routing_key="#")
    channel.basic_consume(queue=Q_NOTIFICATION, on_message_callback=callback, auto_ack=False)
    print(f"[Notification] Waiting for order events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
