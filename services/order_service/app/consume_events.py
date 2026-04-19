"""
Consumer for order_service: listens to payment, inventory, and shipping events from RabbitMQ and updates order status in JSON DB.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from services.order_service.app.services.order_service import OrderService

EXCHANGE_NAME = "order.events"
QUEUE_NAME = "order.update.queue"

status_map = {
    "payment.success": "PAID",
    "payment.failed": "PAYMENT_FAILED",
    "inventory.reserved": "RESERVED",
    "inventory.failed": "INVENTORY_FAILED",
    "order.shipped": "SHIPPED"
}

order_event_state = {}
def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Order] Received event:", event)
    order_id = event["data"].get("order_id")
    if not order_id:
        return
    event_type = event["event"]
    # Track state for each order
    if order_id not in order_event_state:
        order_event_state[order_id] = {"payment": None, "inventory": None, "shipped": False}
    if event_type == "inventory.failed":
        order_event_state[order_id]["inventory"] = "FAILED"
    elif event_type == "inventory.reserved":
        order_event_state[order_id]["inventory"] = "RESERVED"
    elif event_type == "payment.success":
        order_event_state[order_id]["payment"] = "SUCCESS"
    elif event_type == "payment.failed":
        order_event_state[order_id]["payment"] = "FAILED"
    elif event_type == "order.shipped":
        order_event_state[order_id]["shipped"] = True

    # Determine new status
    new_status = None
    state = order_event_state[order_id]
    if state["inventory"] == "FAILED":
        new_status = "INVENTORY_FAILED"
    elif state["payment"] == "FAILED":
        new_status = "PAYMENT_FAILED"
    elif state["payment"] == "SUCCESS" and state["inventory"] == "RESERVED":
        if state["shipped"]:
            new_status = "SHIPPED"
        else:
            new_status = "READY_FOR_SHIPPING"
    elif state["inventory"] == "RESERVED":
        new_status = "RESERVED"

    if new_status:
        try:
            with open(OrderService.JSON_DB_PATH, "r+") as file:
                orders = json.load(file)
                for order in orders:
                    if order["order_id"] == order_id:
                        order["order_status"] = new_status
                        break
                file.seek(0)
                json.dump(orders, file, indent=4)
        except FileNotFoundError:
            pass

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
    declare_queue(QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[Order] Waiting for events to update order status...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
