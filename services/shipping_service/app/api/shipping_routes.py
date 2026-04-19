from services.shipping_service.app.services.shipping_service import ShippingService
from services.shipping_service.app.schemas.shipping_schema import ShippingInput, ShippingOutput

def create_shipment_service(shipping_data: dict) -> dict:
    """
    Accepts shipping input, creates shipment, and returns output event dict.
    """
    return ShippingService.create_shipment(shipping_data)
