# Utility to publish failed messages to DLQ
from .producer import publish_message

def publish_to_dlq(message):
    dlq_exchange = "dlq.events"
    publish_message(dlq_exchange, "", message)
