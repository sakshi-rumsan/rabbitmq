# E-commerce Microservices Application

This project demonstrates an event-driven e-commerce backend using microservices and RabbitMQ for inter-service communication via the Publish–Subscribe (Pub/Sub) pattern.

## Architecture Overview
- **Order Service**: Handles order creation and publishes `order.created` events.
- **Inventory Service**: Listens for order events and reserves inventory.
- **Payment Service**: Listens for order events and processes payments.
- **Notification Service**: Listens for order events and sends notifications.
- **Shipping Service**: (Optional) Handles shipping logic.
- **RabbitMQ**: Message broker for event distribution.

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
2. In separate terminals, run each consumer **from the project root** using Python's module syntax:
   ```bash
   python -m services.payment_service.app.consume_order_created
   python -m services.inventory_service.app.consume_order_created
   python -m services.notification_service.app.consume_order_created
   ```
   This ensures all imports work correctly.

## How to Ingest Data & Trigger Events
- **Create an Order**: Trigger order creation via the Order Service. This can be done by calling the appropriate API endpoint or directly invoking the service logic.
- Example (Python):
   ```python
   from services.order_service.app.api.order_routes import create_order_service
   order_data = {
       "user_id": "user123",
       "items": [{"item_name": "Widget", "quantity": 2}],
       "total_amount": 49.99
   }
   response = create_order_service(order_data)
   print(response)
   ```
- This will:
  - Save the order to a JSON file
  - Publish an `order.created` event to RabbitMQ
  - All listening services (inventory, payment, notification) will receive and process the event

## Testing the Event Flow
1. **Start all services and RabbitMQ** (see above).
2. **Trigger an order creation** (see code above or use an API endpoint if available).
3. **Observe logs/output** in each service's terminal:
   - Inventory service should reserve stock
   - Payment service should process payment
   - Notification service should send/log a notification

## Data Files
- Orders and events are stored in `data/orders.json` and `data/order_events.json`.

## Project Structure
- `services/` — Contains all microservices
- `common/` — Shared messaging and schema code
- `docker-compose.yml` — Multi-service orchestration
- `scripts/` — Helper scripts (start, migrate)
- `docs/` — Pub/Sub documentation and code samples

## Useful Commands
- Build and start all services: `docker-compose up --build`
- Stop all services: `docker-compose down`
- Run a specific consumer: `python services/<service>/app/consume_order_created.py`

## References
- See `docs/pubsub_step1.md`, `docs/pubsub_step1_code.md`, `docs/pubsub_step2_code.md`, and `docs/pubsub_step3_test.md` for detailed event flow and code samples.

---

**Happy hacking!**
