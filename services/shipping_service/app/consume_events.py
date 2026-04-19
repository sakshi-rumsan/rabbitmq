"""
Consumer for shipping_service: listens to payment.success and inventory.reserved events from RabbitMQ and triggers shipment creation.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from services.shipping_service.app.services.shipping_service import ShippingService

EXCHANGE_NAME = "order.events"
QUEUE_NAME = "shipping.queue"

# In-memory state to track order readiness (in production, use persistent storage)
order_state = {}

def callback(ch, method, properties, body):
    event = json.loads(body)
    print("[Shipping] Received event:", event)
    order_id = event["data"].get("order_id")
    if not order_id:
        return
    # Track payment and inventory status
    if order_id not in order_state:
        order_state[order_id] = {"payment": False, "inventory": False}
    if event["event"] == "payment.success":
        order_state[order_id]["payment"] = True
    elif event["event"] == "payment.failed":
        order_state[order_id]["payment"] = False
    if event["event"] == "inventory.reserved":
        order_state[order_id]["inventory"] = True
    elif event["event"] == "inventory.failed":
        order_state[order_id]["inventory"] = False
    # Debug: print and persist order_state
    print(f"[Shipping] Current order_state: {order_state}")
    with open("data/shipping_order_state.json", "w") as f:
        json.dump(order_state, f, indent=4)
    # If both are True, create shipment
    if order_state[order_id]["payment"] and order_state[order_id]["inventory"]:
        ShippingService.create_shipment({"order_id": order_id})
        print(f"[Shipping] Shipment created for order {order_id}")
        # Optionally, remove from state
        del order_state[order_id]

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
    declare_queue(QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[Shipping] Waiting for payment.success and inventory.reserved events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
