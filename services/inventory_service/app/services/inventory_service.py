import json
from datetime import datetime
from typing import Dict, List
from services.inventory_service.app.schemas.inventory_schema import InventoryInput, InventoryReserved, InventoryFailed

class InventoryService:
    EVENTS_DB_PATH = "data/inventory_events.json"
    STOCK_DB_PATH = "data/stock.json"

    @staticmethod
    def reserve_stock(inventory_data: Dict) -> Dict:
        inventory = InventoryInput(**inventory_data)
        # Load stock levels
        try:
            with open(InventoryService.STOCK_DB_PATH, "r") as file:
                stock = json.load(file)
        except FileNotFoundError:
            stock = {}
        # Check and reserve items
        can_reserve = True
        for item in inventory.reserved_items:
            product_id = item["product_id"]
            quantity = item["quantity"]
            if stock.get(product_id, 0) < quantity:
                can_reserve = False
                break
        if can_reserve:
            for item in inventory.reserved_items:
                product_id = item["product_id"]
                quantity = item["quantity"]
                stock[product_id] = stock.get(product_id, 0) - quantity
            with open(InventoryService.STOCK_DB_PATH, "w") as file:
                json.dump(stock, file, indent=4)
            event = InventoryReserved(
                order_id=inventory.order_id,
                reserved_items=inventory.reserved_items
            ).dict()
            InventoryService.publish_event("inventory.reserved", event)
            return event
        else:
            event = InventoryFailed(
                order_id=inventory.order_id,
                reason="Out of stock",
                status="FAILED"
            ).dict()
            InventoryService.publish_event("inventory.failed", event)
            return event

    @staticmethod
    def publish_event(event_name: str, event_data: dict):
        event = {
            "event": event_name,
            "data": event_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            with open(InventoryService.EVENTS_DB_PATH, "r+") as file:
                events = json.load(file)
                events.append(event)
                file.seek(0)
                json.dump(events, file, indent=4)
        except FileNotFoundError:
            with open(InventoryService.EVENTS_DB_PATH, "w") as file:
                json.dump([event], file, indent=4)
