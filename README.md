# E-commerce Microservices Pipeline

An event-driven e-commerce backend built with Python microservices and RabbitMQ. Services communicate exclusively through a **topic exchange** — each service publishes events with a routing key and consumes only the events it cares about from its own durable queue.

---

## Architecture

```
[Order Service]  ──── order.created ────►  [RabbitMQ: pipeline.events (topic exchange)]
                                                    │
              ┌─────────────────────────────────────┼─────────────────────────────────┐
              ▼                                     ▼                                 ▼
   [Inventory Service]                   [Notification Service]              [Order Update Consumer]
   order.created → reserves stock         listens on #                       listens on #
   emits: inventory.reserved/.failed                                         updates orders.json
              │
              ▼
   [Payment Service]
   inventory.reserved → processes payment
   emits: payment.success/.failed
              │
              ├────► [DLQ] (payment.failed)
              ▼
   [Shipping Service]
   waits for BOTH payment.success AND inventory.reserved
   emits: order.shipped
```

### Services

| Service | Queue | Consumes | Publishes |
|---|---|---|---|
| Inventory | `inventory.queue` | `order.created` | `inventory.reserved`, `inventory.failed` |
| Payment | `payment.queue` | `inventory.reserved` | `payment.success`, `payment.failed` |
| Shipping | `shipping.queue` | `payment.success`, `payment.failed`, `inventory.reserved`, `inventory.failed` | `order.shipped` |
| Notification | `notification.queue` | `#` (all events) | — |
| Order Update | `order.update.queue` | `#` (all events) | — |
| DLQ | `dlq.queue` | dead-lettered messages | — |

---

## What Was Fixed (Tasks 01–10)

| # | Fix | Impact |
|---|---|---|
| 01 | RabbitMQ connection reads `RABBITMQ_HOST/PORT/USER/PASS` from environment | Docker works |
| 02 | Payment and Shipping now publish events to RabbitMQ (were writing to JSON only) | Pipeline completes end-to-end |
| 03 | All consumers use manual ack/nack instead of `auto_ack=True` | No silent message loss on crash |
| 04 | Queues, exchanges, and messages are all durable + persistent | State survives broker restart |
| 05 | Replaced fanout exchange with topic exchange + routing keys | Each service only receives its events |
| 06 | Fixed wrong consumer commands in `docker-compose.yml`, added order service | Deployment works |
| 07 | Added `file.truncate()` after every `json.dump` + extracted `common/utils/json_store.py` | No JSON file corruption |
| 08 | Retry logic now uses exponential backoff with jitter (1s, 2s, 4s, 8s, 16s ±25%) | No thundering herd on broker outage |
| 09 | Shipping and order consumers persist state to disk and reload it on startup | Pipeline survives container restarts |
| 10 | Removed dead SQLAlchemy code, renamed files to match their purpose, replaced deprecated `datetime.utcnow()`, removed unused `consumer.py`, `fastapi`/`uvicorn` from requirements | Clean, accurate codebase |

---

## Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- Python 3.10+ (only needed for local runs without Docker)

---

## Quick Start (Docker)

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd ecommerce

# 2. Configure environment (defaults work for local Docker)
cp .env .env.local   # optional — edit if you need custom credentials

# 3. Build and start everything
docker-compose up --build
```

All six services and RabbitMQ start automatically. Wait for the healthcheck to pass (you'll see `[*] Waiting for messages` in each service's logs), then trigger an order:

```bash
# In a second terminal
export PYTHONPATH=$(pwd)
python scripts/trigger_order.py
```

Watch the service logs — you should see the full chain:
```
[Inventory]    Reserving stock for: ...
[Payment]      Processing inventory.reserved event: ...
[Shipping]     Shipment created for order <id>
[Notification] Received event: order.shipped
[Order]        Received event: order.shipped
```

**RabbitMQ management UI:** http://localhost:15672 (guest / guest)

---

## Running Locally (Without Docker)

**1. Start RabbitMQ**

```bash
docker run -d --name rabbitmq \
  -p 5672:5672 -p 15672:15672 \
  rabbitmq:3-management
```

**2. Install dependencies**

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

**3. Run everything with one command**

```bash
python scripts/run.py
```

`run.py` starts all six consumers in the background, waits for them to connect, creates all test orders, then shows a live pipeline trace — no manual setup needed.

```
E-Commerce Pipeline Runner
────────────────────────────────────────

Starting consumers…
  ▶ Inventory  consumer started  (PID 12301 → logs/inventory.log)
  ▶ Payment    consumer started  (PID 12302 → logs/payment.log)
  ...

══════════════════════════════════════════════════════════════
  PIPELINE TRACE                                    14:03:21
══════════════════════════════════════════════════════════════

  Order a1b2c3d4…   user=user123  $99.99
  Status › SHIPPED
  [✓ Created] → [✓ Inventory] → [✓ Payment] → [✓ Shipped]

  Order e5f6a7b8…   user=user456  $1200.0
  Status › PAYMENT_FAILED
  [✓ Created] → [✓ Inventory] → [✗ Payment] → [─ Shipped]
```

Consumer logs are written to `logs/<service>.log` to keep the terminal clean.

> **Manual start (advanced):** if you need to run consumers individually, set `PYTHONPATH=$(pwd)` and start each script directly:
> ```bash
> python services/inventory_service/app/consume_order_created.py
> python services/payment_service/app/consume_inventory_reserved.py
> python services/shipping_service/app/consume_events.py
> python services/notification_service/app/consume_events.py
> python services/order_service/app/consume_events.py
> python common/messaging/consume_dlq.py
> # then in another terminal:
> python scripts/trigger_order.py
> ```

---

## Test Scenarios

The `data/dummy_order.json` file contains four pre-built orders that exercise different pipeline paths:

| Order | `total_amount` | Expected outcome |
|---|---|---|
| user123 | $99.99 | Payment succeeds → shipped |
| user456 | $1200.00 | Payment fails (>$1000 limit) → DLQ |
| user789 | $500.00 | Payment succeeds → shipped |
| user321 | $1500.00 | Payment fails → DLQ |

`trigger_order.py` cycles through all four in sequence.

---

## Inspecting Results

All events are written to JSON files in `data/` for debugging:

| File | Contents |
|---|---|
| `data/orders.json` | Orders with current status (`PENDING` → `SHIPPED` / `PAYMENT_FAILED`) |
| `data/order_events.json` | Events published by the Order Service |
| `data/inventory_events.json` | Events published by the Inventory Service |
| `data/payment_events.json` | Events published by the Payment Service |
| `data/shipping_events.json` | Events published by the Shipping Service |
| `data/notification_events.json` | Notification log |
| `data/dlq_events.json` | Failed messages routed to the Dead Letter Queue |
| `data/shipping_order_state.json` | Persisted saga state for the Shipping Service |
| `data/order_event_state.json` | Persisted saga state for the Order Update consumer |

---

## Project Structure

```
ecommerce/
├── common/
│   ├── messaging/
│   │   ├── connection.py          # RabbitMQ connection (reads env vars, retries)
│   │   ├── producer.py            # publish_message helper
│   │   ├── exchanges.py           # declare_exchange (accepts optional channel)
│   │   ├── queues.py              # declare_queue (accepts optional channel)
│   │   ├── constants.py           # exchange/queue/routing-key names
│   │   ├── retry.py               # exponential backoff retry for publish failures
│   │   ├── dlq.py                 # publish_to_dlq helper
│   │   ├── consume_dlq.py         # DLQ consumer
│   │   └── setup_retry_infrastructure.py  # RabbitMQ retry queue pattern
│   └── utils/
│       └── json_store.py          # append_to_json_file (safe seek+dump+truncate)
├── services/
│   ├── order_service/app/
│   │   ├── services/order_service.py
│   │   └── consume_events.py      # listens on # — updates order status
│   ├── inventory_service/app/
│   │   ├── services/inventory_service.py
│   │   └── consume_order_created.py
│   ├── payment_service/app/
│   │   ├── services/payment_service.py
│   │   └── consume_inventory_reserved.py
│   ├── shipping_service/app/
│   │   ├── services/shipping_service.py
│   │   └── consume_events.py      # saga: waits for payment + inventory
│   └── notification_service/app/
│       ├── services/notification_service.py
│       └── consume_events.py
├── data/                          # runtime JSON files (gitignored except stock.json)
├── scripts/
│   └── trigger_order.py
├── docker-compose.yml
├── requirements.txt
└── .env                           # RABBITMQ_HOST/PORT/USER/PASS
```

---

## Useful Commands

```bash
# Start everything
docker-compose up --build

# Stop and remove containers
docker-compose down

# Stop and wipe volumes (resets RabbitMQ queues)
docker-compose down -v

# Tail logs for one service
docker-compose logs -f payment_service

# Rebuild a single service after a code change
docker-compose up --build payment_service
```
