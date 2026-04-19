# Step 2: Queue Bindings & Consumers (Code)

## What was done
- Added a consumer script for each service (payment, inventory, notification) to:
  - Declare its own queue (e.g., `payment.queue`, `inventory.queue`, `notification.queue`).
  - Bind the queue to the `order.events` fanout exchange.
  - Consume `order.created` events and trigger the appropriate service logic.

## Key Files
- `services/payment_service/app/consume_order_created.py`
- `services/inventory_service/app/consume_order_created.py`
- `services/notification_service/app/consume_order_created.py`

## Example (Payment Service)
```python
EXCHANGE_NAME = "order.events"
QUEUE_NAME = "payment.queue"

declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
declare_queue(QUEUE_NAME)
channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)

# Consume and process order.created events
```

- Each service now independently reacts to the same event, following the Pub/Sub pattern.

---

Next: Test the full event flow and document the results.
