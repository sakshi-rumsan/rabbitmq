import json
from datetime import datetime
from typing import Dict, List

class InventoryService:
    EVENTS_DB_PATH = "data/inventory_events.json"
    STOCK_DB_PATH = "data/stock.json"

    @staticmethod
    def reserve_stock(inventory_data: Dict) -> Dict:
        print(f"[InventoryService] Reserving stock for: {inventory_data}")
        # Load stock levels
        try:
            with open(InventoryService.STOCK_DB_PATH, "r") as file:
                stock = json.load(file)
        except FileNotFoundError:
            stock = {}
        # Check and reserve items
        can_reserve = True
        for item in inventory_data["reserved_items"]:
            product_id = item["product_id"]
            quantity = item["quantity"]
            if stock.get(product_id, 0) < quantity:
                can_reserve = False
                break
        if can_reserve:
            for item in inventory_data["reserved_items"]:
                product_id = item["product_id"]
                quantity = item["quantity"]
                stock[product_id] = stock.get(product_id, 0) - quantity
            with open(InventoryService.STOCK_DB_PATH, "w") as file:
                json.dump(stock, file, indent=4)
            event = {
                "order_id": inventory_data["order_id"],
                "user_id": inventory_data.get("user_id"),
                "total_amount": inventory_data.get("total_amount"),
                "reserved_items": inventory_data["reserved_items"]
            }
            InventoryService.publish_event("inventory.reserved", event)
            return {"status": "reserved", "data": event}
        else:
            event = {
                "order_id": inventory_data["order_id"],
                "user_id": inventory_data.get("user_id"),
                "total_amount": inventory_data.get("total_amount"),
                "reason": "Out of stock",
                "status": "FAILED"
            }
            InventoryService.publish_event("inventory.failed", event)
            return {"status": "failed", "data": event}

    @staticmethod
    def publish_event(event_name: str, event_data: dict):
        import pika
        event = {
            "event": event_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        # Publish to RabbitMQ exchange
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters("localhost"))
            channel = connection.channel()
            channel.exchange_declare(exchange="order.events", exchange_type="fanout")
            channel.basic_publish(
                exchange="order.events",
                routing_key="",
                body=json.dumps(event)
            )
            connection.close()
        except Exception as e:
            print(f"[InventoryService] Failed to publish event to RabbitMQ: {e}")
        # Also write to JSON file for debugging
        try:
            with open(InventoryService.EVENTS_DB_PATH, "r+") as file:
                events = json.load(file)
                events.append(event)
                file.seek(0)
                json.dump(events, file, indent=4)
        except FileNotFoundError:
            with open(InventoryService.EVENTS_DB_PATH, "w") as file:
                json.dump([event], file, indent=4)
