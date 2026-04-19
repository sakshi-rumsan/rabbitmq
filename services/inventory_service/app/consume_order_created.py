"""
Consumer for inventory_service: listens to order.created events from RabbitMQ and triggers inventory reservation.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from services.inventory_service.app.services.inventory_service import InventoryService


EXCHANGE_NAME = "order.events"
QUEUE_NAME = "inventory.queue"

def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Inventory] Received event:", event)
    if event.get("event") == "order.created":
        order = event["data"]
        inventory_data = {
            "order_id": order["order_id"],
            "user_id": order.get("user_id"),
            "total_amount": order.get("total_amount"),
            "reserved_items": [
                {"product_id": item["item_name"], "quantity": item["quantity"]}
                for item in order["items"]
            ]
        }
        InventoryService.reserve_stock(inventory_data)

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
    declare_queue(QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[Inventory] Waiting for order.created events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()