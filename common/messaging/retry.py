# RabbitMQ message retry logic
from .producer import publish_message

def retry_message(exchange, routing_key, message, max_retries=5):
    for attempt in range(max_retries):
        try:
            publish_message(exchange, routing_key, message)
            break
        except Exception as e:
            print(f"Retry {attempt + 1}/{max_retries} failed: {e}")
            if attempt == max_retries - 1:
                raise