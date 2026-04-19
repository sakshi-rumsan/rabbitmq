# Step 3: Test and Document Full Pub/Sub Event Flow

## What to Test
- When an order is created, the `order.created` event should be published to RabbitMQ.
- All three services (payment, inventory, notification) should receive the event via their queues and process it independently.

## How to Test
1. Start RabbitMQ and all services.
2. Run each consumer script:
   - `python services/payment_service/app/consume_order_created.py`
   - `python services/inventory_service/app/consume_order_created.py`
   - `python services/notification_service/app/consume_order_created.py`
3. Trigger an order creation (e.g., via API or direct call).
4. Observe logs/output for each service to confirm event receipt and processing.

## Expected Results
- All services log or process the `order.created` event.
- Payment and inventory services process the order data.
- Notification service sends/logs a notification for the order.

---

This completes the basic Pub/Sub event flow for order creation using RabbitMQ.
