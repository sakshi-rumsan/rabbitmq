from datetime import datetime, timezone
from services.notification_service.app.schemas.notification_schema import NotificationInput, NotificationSent
from common.utils.json_store import append_to_json_file

class NotificationService:
    NOTIFY_DB_PATH = "data/notification_events.json"
    EVENT_MESSAGES = {
        "order.created": "Order received",
        "payment.success": "Payment confirmed",
        "payment.failed": "Payment failed",
        "inventory.failed": "Out of stock",
        "order.shipped": "Your order is shipped"
    }

    @staticmethod
    def send_notification(notification_data: dict) -> dict:
        notif = NotificationInput(**notification_data)
        message = NotificationService.EVENT_MESSAGES.get(notif.event, "Notification")
        event = NotificationSent(
            order_id=notif.order_id,
            event=notif.event,
            message=message
        ).dict()
        NotificationService.log_notification(event)
        return event

    @staticmethod
    def log_notification(event_data: dict):
        event = {
            "event": "notification.sent",
            "data": event_data,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        append_to_json_file(NotificationService.NOTIFY_DB_PATH, event)
