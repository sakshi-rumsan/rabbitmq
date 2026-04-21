"""
Consumer for shipping_service: listens to payment and inventory events from RabbitMQ and triggers shipment creation.
"""
import json
import os
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

STATE_FILE = "data/shipping_order_state.json"


def load_state() -> dict:
    """Load persisted order state from disk, or return empty dict."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("[Shipping] Warning: could not read state file, starting fresh.")
    return {}


def save_state(state: dict) -> None:
    """Persist order state to disk."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


# Load state at module level so it survives reconnects within the same process
order_state = load_state()


def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        print("[Shipping] Received event:", event)
        order_id = event["data"].get("order_id")
        if not order_id:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        if order_id not in order_state:
            order_state[order_id] = {"payment": False, "inventory": False}

        if event["event"] == RK_PAYMENT_SUCCESS:
            order_state[order_id]["payment"] = True
        elif event["event"] == RK_PAYMENT_FAILED:
            order_state[order_id]["payment"] = False
        elif event["event"] == RK_INVENTORY_RESERVED:
            order_state[order_id]["inventory"] = True
        elif event["event"] == RK_INVENTORY_FAILED:
            order_state[order_id]["inventory"] = False

        save_state(order_state)
        print(f"[Shipping] Current order_state: {order_state}")

        if order_state[order_id]["payment"] and order_state[order_id]["inventory"]:
            ShippingService.create_shipment({"order_id": order_id})
            print(f"[Shipping] Shipment created for order {order_id}")
            del order_state[order_id]
            save_state(order_state)

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[Shipping] Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)
    declare_queue(Q_SHIPPING)
    for routing_key in [RK_PAYMENT_SUCCESS, RK_PAYMENT_FAILED, RK_INVENTORY_RESERVED, RK_INVENTORY_FAILED]:
        channel.queue_bind(exchange=PIPELINE_EXCHANGE, queue=Q_SHIPPING, routing_key=routing_key)
    channel.basic_consume(queue=Q_SHIPPING, on_message_callback=callback, auto_ack=False)
    print(f"[Shipping] Waiting for payment and inventory events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
