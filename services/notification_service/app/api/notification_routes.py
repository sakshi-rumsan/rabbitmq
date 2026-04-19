from services.notification_service.app.services.notification_service import NotificationService
from services.notification_service.app.schemas.notification_schema import NotificationInput, NotificationSent

def send_notification_service(notification_data: dict) -> dict:
    """
    Accepts notification input, sends notification, and returns output event dict.
    """
    return NotificationService.send_notification(notification_data)
