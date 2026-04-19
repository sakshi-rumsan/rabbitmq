from services.inventory_service.app.services.inventory_service import InventoryService
from services.inventory_service.app.schemas.inventory_schema import InventoryInput, InventoryReserved, InventoryFailed

def reserve_inventory_service(inventory_data: dict) -> dict:
    """
    Accepts inventory input, reserves stock, and returns output event dict.
    """
    return InventoryService.reserve_stock(inventory_data)
