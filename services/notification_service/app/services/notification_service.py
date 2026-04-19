import json
from datetime import datetime
from services.notification_service.app.schemas.notification_schema import NotificationInput, NotificationSent

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
            "timestamp": datetime.utcnow().isoformat()
        }
        try:
            with open(NotificationService.NOTIFY_DB_PATH, "r+") as file:
                events = json.load(file)
                events.append(event)
                file.seek(0)
                json.dump(events, file, indent=4)
        except FileNotFoundError:
            with open(NotificationService.NOTIFY_DB_PATH, "w") as file:
                json.dump([event], file, indent=4)
