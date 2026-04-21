#!/usr/bin/env python3
"""
Run all consumers and trigger orders with a live pipeline trace.

Usage (from project root):
    python scripts/run.py
"""
import os
import sys
import json
import time
import signal
import subprocess
from pathlib import Path
from datetime import datetime

# ── ANSI helpers ──────────────────────────────────────────────────────────────
G   = "\033[92m"   # green
R   = "\033[91m"   # red
Y   = "\033[93m"   # yellow
C   = "\033[96m"   # cyan
B   = "\033[1m"    # bold
D   = "\033[2m"    # dim
RST = "\033[0m"

def clr():
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()

# ── Consumer definitions ───────────────────────────────────────────────────────
CONSUMERS = [
    ("Inventory",    "services/inventory_service/app/consume_order_created.py"),
    ("Payment",      "services/payment_service/app/consume_inventory_reserved.py"),
    ("Shipping",     "services/shipping_service/app/consume_events.py"),
    ("Notification", "services/notification_service/app/consume_events.py"),
    ("Order",        "services/order_service/app/consume_events.py"),
    ("DLQ",          "common/messaging/consume_dlq.py"),
]

ORDER_STATE_FILE = "data/order_event_state.json"
ORDERS_FILE      = "data/orders.json"
LOG_DIR          = Path("logs")

_procs: list[tuple[str, subprocess.Popen]] = []

# ── Env & startup ─────────────────────────────────────────────────────────────
def setup_env():
    os.environ.setdefault("RABBITMQ_HOST", "localhost")
    os.environ.setdefault("RABBITMQ_PORT", "5672")
    os.environ.setdefault("RABBITMQ_USER", "guest")
    os.environ.setdefault("RABBITMQ_PASS", "guest")
    os.environ["PYTHONPATH"] = str(Path.cwd())


def start_consumers():
    LOG_DIR.mkdir(exist_ok=True)
    env = os.environ.copy()
    for name, script in CONSUMERS:
        log_path = LOG_DIR / f"{name.lower()}.log"
        log_fh   = open(log_path, "w")
        proc = subprocess.Popen(
            [sys.executable, script],
            stdout=log_fh,
            stderr=log_fh,
            env=env,
        )
        _procs.append((name, proc, log_fh))
        print(f"  {G}▶{RST} {B}{name}{RST} consumer started  {D}(PID {proc.pid} → logs/{name.lower()}.log){RST}")


def shutdown(sig=None, frame=None):
    print(f"\n{Y}Stopping consumers…{RST}")
    for name, proc, fh in _procs:
        proc.terminate()
        fh.close()
        print(f"  {R}■{RST} {name} stopped")
    sys.exit(0)

# ── JSON helpers ──────────────────────────────────────────────────────────────
def load_json(path: str):
    p = Path(path)
    if not (p.exists() and p.stat().st_size > 0):
        return None
    try:
        with open(p) as f:
            return json.load(f)
    except Exception:
        return None

# ── Stage rendering ───────────────────────────────────────────────────────────
def _badge(label: str, state: str) -> str:
    """Return a coloured badge for a pipeline stage."""
    if state == "ok":
        return f"{G}{B}[✓ {label}]{RST}"
    if state == "fail":
        return f"{R}{B}[✗ {label}]{RST}"
    if state == "skip":
        return f"{D}[─ {label}]{RST}"
    return f"{Y}[… {label}]{RST}"          # pending


def _status_color(status: str) -> str:
    if "FAILED"  in status: return R
    if status in ("SHIPPED",):              return G
    if status in ("READY_FOR_SHIPPING", "RESERVED"): return C
    return Y


def render(order_state: dict, orders_map: dict, order_ids: list[str]) -> str:
    lines = []
    now   = datetime.now().strftime("%H:%M:%S")
    bar   = "═" * 62

    lines += [
        f"\n{C}{B}{bar}{RST}",
        f"{C}{B}  PIPELINE TRACE{RST}                          {D}{now}{RST}",
        f"{C}{B}{bar}{RST}",
    ]

    for oid in order_ids:
        order  = orders_map.get(oid, {})
        state  = order_state.get(oid, {})
        user   = order.get("user_id",      oid[:8])
        amount = order.get("total_amount", "?")
        status = order.get("order_status", "PENDING")

        inv     = state.get("inventory")
        pay     = state.get("payment")
        shipped = state.get("shipped", False)

        inv_s   = "ok" if inv == "RESERVED"  else ("fail" if inv == "FAILED" else "pending")
        pay_s   = "ok" if pay == "SUCCESS"   else ("fail" if pay == "FAILED" else "pending")
        ship_s  = "ok" if shipped else ("skip" if (pay == "FAILED" or inv == "FAILED") else "pending")

        lines += [
            f"\n  {B}Order {oid[:8]}…{RST}   {D}user={user}  ${amount}{RST}",
            f"  Status › {_status_color(status)}{B}{status}{RST}",
            (
                f"  "
                + _badge("Created",   "ok")
                + f" {D}→{RST} "
                + _badge("Inventory", inv_s)
                + f" {D}→{RST} "
                + _badge("Payment",   pay_s)
                + f" {D}→{RST} "
                + _badge("Shipped",   ship_s)
            ),
        ]

    # Consumer health
    lines += ["", f"  {D}{'─'*58}{RST}", f"  {D}Consumers:{RST}"]
    for name, proc, _ in _procs:
        alive = proc.poll() is None
        dot   = f"{G}●{RST}" if alive else f"{R}●{RST}"
        lines.append(f"    {dot} {D}{name}{RST}")

    lines += [
        f"\n{C}{B}{bar}{RST}",
        f"{D}Logs → logs/   |   Ctrl+C to stop{RST}\n",
    ]
    return "\n".join(lines)


def is_terminal(state: dict) -> bool:
    """True when an order has reached a final pipeline state."""
    return (
        state.get("shipped") is True
        or state.get("payment")   == "FAILED"
        or state.get("inventory") == "FAILED"
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    setup_env()
    signal.signal(signal.SIGINT,  shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    print(f"\n{C}{B}E-Commerce Pipeline Runner{RST}")
    print(f"{C}{'─'*40}{RST}\n")

    print(f"{B}Starting consumers…{RST}")
    start_consumers()

    print(f"\n{D}Waiting 3 s for consumers to connect to RabbitMQ…{RST}")
    time.sleep(3)

    print(f"\n{B}Creating orders…{RST}")
    with open("data/dummy_order.json") as f:
        orders_data = json.load(f)
    if isinstance(orders_data, dict):
        orders_data = [orders_data]

    from services.order_service.app.api.order_routes import create_order_service
    order_ids: list[str] = []
    for od in orders_data:
        resp = create_order_service(od)
        oid  = resp.get("order_id", "")
        order_ids.append(oid)
        print(f"  {G}✓{RST} {oid[:8]}…  user={od['user_id']}  ${od['total_amount']}")

    print(f"\n{B}Watching pipeline (60 s timeout)…{RST}")
    time.sleep(1)

    deadline = time.time() + 60
    while time.time() < deadline:
        order_state = load_json(ORDER_STATE_FILE) or {}
        orders_raw  = load_json(ORDERS_FILE) or []
        orders_map  = (
            {o["order_id"]: o for o in orders_raw}
            if isinstance(orders_raw, list)
            else {}
        )

        for oid in list(order_state):
            if oid not in order_ids:
                order_ids.append(oid)

        clr()
        print(render(order_state, orders_map, order_ids), end="", flush=True)

        all_done = bool(order_ids) and all(
            is_terminal(order_state.get(oid, {})) for oid in order_ids
        )
        if all_done:
            print(f"\n{G}{B}All orders reached terminal state.{RST}\n")
            break

        time.sleep(1)

    print(f"{Y}Consumers still running. Press Ctrl+C to stop.{RST}")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()


if __name__ == "__main__":
    main()
