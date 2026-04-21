"""
Consumer for order_service: listens to all pipeline events from RabbitMQ and updates order status in JSON DB.
"""
import json
import os
from pathlib import Path
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from common.messaging.constants import PIPELINE_EXCHANGE, EXCHANGE_TYPE, Q_ORDER_UPDATE
from common.messaging.setup_retry_infrastructure import setup_retry_infrastructure
from services.order_service.app.services.order_service import OrderService
from common.utils.json_store import append_to_json_file

STATE_FILE = "data/order_event_state.json"


def load_state() -> dict:
    """Load persisted order event state from disk, or return empty dict."""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            print("[Order] Warning: could not read state file, starting fresh.")
    return {}


def save_state(state: dict) -> None:
    """Persist order event state to disk."""
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=4)


# Load state at module level so it survives reconnects within the same process
order_event_state = load_state()


def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
        print("[Order] Received event:", event)
        order_id = event["data"].get("order_id")
        if not order_id:
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        event_type = event["event"]
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

        save_state(order_event_state)

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
            path = Path(OrderService.JSON_DB_PATH)
            if path.exists():
                with open(path, "r+") as file:
                    orders = json.load(file)
                    for order in orders:
                        if order["order_id"] == order_id:
                            order["order_status"] = new_status
                            break
                    file.seek(0)
                    json.dump(orders, file, indent=4)
                    file.truncate()

        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        print(f"[Order] Error processing message: {e}")
        ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)


def main():
    setup_retry_infrastructure(
        work_queue=Q_ORDER_UPDATE,
        exchange=PIPELINE_EXCHANGE,
        routing_key="#",
    )
    connection = get_connection()
    channel = connection.channel()
    channel.basic_qos(prefetch_count=1)
    declare_exchange(PIPELINE_EXCHANGE, exchange_type=EXCHANGE_TYPE)
    channel.queue_bind(exchange=PIPELINE_EXCHANGE, queue=Q_ORDER_UPDATE, routing_key="#")
    channel.basic_consume(queue=Q_ORDER_UPDATE, on_message_callback=callback, auto_ack=False)
    print(f"[Order] Waiting for events to update order status...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
