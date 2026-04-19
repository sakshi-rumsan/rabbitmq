# Step 1: Pub/Sub Pattern Implementation (Code)

## What was done
- Updated `OrderService.publish_event` in `services/order_service/app/services/order_service.py` to publish the `order.created` event to a RabbitMQ exchange using the Pub/Sub (fanout) pattern.
- Used the `common.messaging.producer.publish_message` and `common.messaging.exchanges.declare_exchange` utilities to ensure the event is sent to a fanout exchange (`order.events`).

## Key Code
```python
from common.messaging.producer import publish_message
from common.messaging.exchanges import declare_exchange

exchange_name = "order.events"
declare_exchange(exchange_name, exchange_type="fanout")

# ...
publish_message(exchange=exchange_name, routing_key="", message=message)
```

- This ensures that when an order is created, the event is broadcast to all bound queues (e.g., payment, inventory, notification) for further processing by other services.

---

Next: Bind queues and set up consumers for each service.
