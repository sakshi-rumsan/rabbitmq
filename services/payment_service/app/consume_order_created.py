"""
Consumer for payment_service: listens to order.created events from RabbitMQ and triggers payment processing.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from services.payment_service.app.services.payment_service import PaymentService

EXCHANGE_NAME = "order.events"
QUEUE_NAME = "payment.queue"

def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Payment] Received event:", event)
    if event.get("event") == "order.created":
        PaymentService.process_payment(event["data"])

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
    declare_queue(QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[Payment] Waiting for order.created events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()