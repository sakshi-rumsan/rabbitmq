
# E-commerce Microservices Application

This project is an event-driven e-commerce backend built with Python microservices and RabbitMQ, using the Publish–Subscribe (Pub/Sub) pattern for inter-service communication. It demonstrates a robust, decoupled architecture for order processing, inventory management, payment, shipping, and notifications.


## Architecture Overview

- **Order Service**: Handles order creation via API, saves orders, and publishes `order.created` events. Listens for downstream events to update order status.
- **Inventory Service**: Listens for `order.created`, checks/reserves stock, emits `inventory.reserved` or `inventory.failed`.
- **Payment Service**: Listens for `inventory.reserved`, processes payment, emits `payment.success` or `payment.failed`.
- **Shipping Service**: Listens for both `payment.success` and `inventory.reserved`, creates shipment, emits `order.shipped`.
- **Notification Service**: Listens for all major events and sends/logs notifications.
- **DLQ (Dead Letter Queue)**: Captures failed payment/inventory events for inspection.
- **RabbitMQ**: Message broker for event distribution using a fanout exchange (pub/sub).

### Event Flow
1. **Order Service** receives API request, creates order, publishes `order.created`.
2. **Inventory Service** reserves stock, emits `inventory.reserved` or `inventory.failed`.
3. **Payment Service** processes payment after inventory is reserved, emits `payment.success` or `payment.failed`.
4. **Shipping Service** creates shipment when both payment and inventory are successful, emits `order.shipped`.
5. **Notification Service** logs/sends notifications for all major events.
6. **Order Service** updates order status based on events.
7. **DLQ** stores failed events for debugging.

---

## Architecture Flowchart
```
graph TD
   A[Order Service] -- order.created --> B[Inventory Service]
   A -- order.created --> C[Payment Service]
   A -- order.created --> D[Notification Service]
   B -- inventory.reserved / inventory.failed --> C
   B -- inventory.reserved / inventory.failed --> D
   C -- payment.success / payment.failed --> E[Shipping Service]
   C -- payment.success / payment.failed --> D
   E -- order.shipped --> D
   E -- order.shipped --> A
   B -- inventory.failed --> F[DLQ]
   C -- payment.failed --> F
   D -- notification.sent --> G[User]
   subgraph Message Broker (RabbitMQ)
      A
      B
      C
      D
      E
   end
```


## Prerequisites
- Python 3.8+
- [Docker](https://www.docker.com/get-started) & Docker Compose
- (Optional) Local virtual environment: `python -m venv .venv`


## Setup & Installation

1. **Clone the repository** and navigate to the project root:
   ```bash
   git clone <repo-url>
   cd ecommerce
   ```

2. **Install Python dependencies** (if running locally):
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Start RabbitMQ and all services using Docker Compose:**
   ```bash
   docker-compose up --build
   ```
   This will start RabbitMQ and all microservices, each running its consumer script.


## Running Services Manually (Alternative)
1. Start RabbitMQ (via Docker or locally).
2. In separate terminals, run each consumer from the project root (set PYTHONPATH):
   ```bash
   export PYTHONPATH=$PYTHONPATH:$(pwd)
   python3 services/inventory_service/app/consume_order_created.py &
   python3 services/payment_service/app/consume_order_created.py &
   python3 services/shipping_service/app/consume_events.py &
   python3 services/order_service/app/consume_events.py &
   python3 services/notification_service/app/consume_order_created.py &
   python3 common/messaging/consume_dlq.py &
   ```
   This ensures all event consumers and DLQ handler are running.
3. Alternatively, run each consumer using Python's module syntax:
   ```bash
   python -m services.payment_service.app.consume_order_created
   python -m services.inventory_service.app.consume_order_created
   python -m services.notification_service.app.consume_order_created
   ```
   This ensures all imports work correctly.


## How to Ingest Data & Trigger Events

### 1. Trigger an Order (Start the Flow)
You can trigger an order using the provided script:
```bash
export PYTHONPATH=$PYTHONPATH:$(pwd)
python3 scripts/trigger_order.py
```
This will:
- Read order data from `data/dummy_order.json`
- Call the Order Service to create the order
- Save the order to `data/orders.json`
- Publish an `order.created` event to RabbitMQ

### 2. Payment & Inventory Processing
The Payment and Inventory services automatically listen for `order.created` events:
- **Payment Service**: Processes payment and publishes `payment.success` or `payment.failed`.
- **Inventory Service**: Reserves stock and publishes `inventory.reserved` or `inventory.failed`.

### 3. Shipping Service
The Shipping Service waits for both `payment.success` and `inventory.reserved` for an order, then creates a shipment and publishes `order.shipped`.

### 4. Order Status Update
The Order Service listens for all relevant events and updates the order status in `data/orders.json`.

### 5. Notification Service
The Notification Service listens for all events and logs/sends notifications.

### 6. Dead Letter Queue (DLQ)
If payment or inventory fails, the failed event is published to the DLQ and stored in `data/dlq_events.json` for inspection.

---

**Summary of Steps:**
1. Start RabbitMQ and all consumers (see above)
2. Trigger an order: `python3 scripts/trigger_order.py`
3. The rest of the flow is automatic via events and consumers
4. Inspect JSON files in `data/` for results and logs

---

**Happy hacking!**


## Testing the Event Flow
1. **Start all services and RabbitMQ** (see above).
2. **Trigger an order creation** (see code above or use an API endpoint if available).
3. **Observe logs/output** in each service's terminal:
   - Inventory service should reserve stock
   - Payment service should process payment
   - Notification service should send/log a notification

## Data Files
- Orders and events are stored in `data/orders.json`, `data/order_events.json`, and other JSON files in `data/`.


## Project Structure
- `services/` — All microservices (order, inventory, payment, shipping, notification)
- `common/` — Shared messaging, event schemas, and utilities
- `data/` — JSON files for events, orders, stock, DLQ, etc.
- `docker-compose.yml` — Multi-service orchestration
- `scripts/` — Helper scripts (start, migrate, trigger order)
- `docs/` — Pub/Sub documentation and code samples


## Useful Commands
- Build and start all services: `docker-compose up --build`
- Stop all services: `docker-compose down`
- Run a specific consumer: `python services/<service>/app/consume_order_created.py`


## References
- See `docs/pubsub_step1.md`, `docs/pubsub_step1_code.md`, `docs/pubsub_step2_code.md`, and `docs/pubsub_step3_test.md` for detailed event flow and code samples.

---

**Happy hacking!**
