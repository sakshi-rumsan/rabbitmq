"""
Consumer for shipping_service: listens to payment and inventory events from RabbitMQ and triggers shipment creation.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from common.messaging.constants import (
    PIPELINE_EXCHANGE, EXCHANGE_TYPE,
    RK_PAYMENT_SUCCESS, RK_PAYMENT_FAILED,
    RK_INVENTORY_RESERVED, RK_INVENTORY_FAILED,
    Q_SHIPPING
)
from services.shipping_service.app.services.shipping_service import ShippingService

# In-memory state to track order readiness (in production, use persistent storage)
order_state = {}

def callback(_ch, _method, _properties, body):
    event = json.loads(body)
    print("[Shipping] Received event:", event)
    order_id = event["data"].get("order_id")
    if not order_id:
        return
    if order_id not in order_state:
        order_state[order_id] = {"payment": False, "inventory": False}
    if event["event"] == RK_PAYMENT_SUCCESS:
        order_state[order_id]["payment"] = True
    elif event["event"] == RK_PAYMENT_FAILED:
        order_state[order_id]["payment"] = False
    if event["event"] == RK_INVENTORY_RESERVED:
        order_state[order_id]["inventory"] = True
    elif event["event"] == RK_INVENTORY_FAILED:
        order_state[order_id]["inventory"] = False
    print(f"[Shipping] Current order_state: {order_state}")
    with open("data/shipping_order_state.json", "w") as f:
        json.dump(order_state, f, indent=4)
    if order_state[order_id]["payment"] and order_state[order_id]["inventory"]:
        ShippingService.create_shipment({"order_id": order_id})
        print(f"[Shipping] Shipment created for order {order_id}")
        del order_state[order_id]

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)
    declare_queue(Q_SHIPPING)
    for routing_key in [RK_PAYMENT_SUCCESS, RK_PAYMENT_FAILED, RK_INVENTORY_RESERVED, RK_INVENTORY_FAILED]:
        channel.queue_bind(exchange=PIPELINE_EXCHANGE, queue=Q_SHIPPING, routing_key=routing_key)
    channel.basic_consume(queue=Q_SHIPPING, on_message_callback=callback, auto_ack=True)
    print(f"[Shipping] Waiting for payment and inventory events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
