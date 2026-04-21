"""
Consumer for payment_service: listens to inventory.reserved events from RabbitMQ and triggers payment processing.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from common.messaging.constants import PIPELINE_EXCHANGE, EXCHANGE_TYPE, RK_INVENTORY_RESERVED, Q_PAYMENT
from services.payment_service.app.services.payment_service import PaymentService


def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Payment] Processing inventory.reserved event:", event)
    PaymentService.process_payment(event["data"])

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)
    declare_queue(Q_PAYMENT)
    channel.queue_bind(exchange=PIPELINE_EXCHANGE, queue=Q_PAYMENT, routing_key=RK_INVENTORY_RESERVED)
    channel.basic_consume(queue=Q_PAYMENT, on_message_callback=callback, auto_ack=True)
    print(f"[Payment] Waiting for inventory.reserved events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
