from services.payment_service.app.services.payment_service import PaymentService
from services.payment_service.app.schemas.payment_schema import PaymentInput, PaymentSuccess, PaymentFailed

def process_payment_service(payment_data: dict) -> dict:
    """
    Accepts payment input, processes payment, and returns output event dict.
    """
    return PaymentService.process_payment(payment_data)
