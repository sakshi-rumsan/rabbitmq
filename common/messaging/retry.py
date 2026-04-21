import time
import random
from .producer import publish_message


def retry_message(
    exchange: str,
    routing_key: str,
    message: str,
    max_retries: int = 5,
    base_delay: float = 1.0,
) -> None:
    """
    Publish a message with exponential backoff and jitter.

    Use this only for producer-side publish failures (e.g. broker briefly
    unreachable when calling publish_message). For consumer-side processing
    failures, prefer basic_nack(requeue=False) and let RabbitMQ route the
    message to the dead letter exchange — that keeps timing and retry counts
    inside the broker instead of the application.
    """
    for attempt in range(1, max_retries + 1):
        try:
            publish_message(exchange, routing_key, message)
            return
        except Exception as e:
            if attempt == max_retries:
                print(f"[Retry] All {max_retries} attempts failed. Giving up: {e}")
                raise
            # Exponential backoff: 1s, 2s, 4s, 8s... with ±25% jitter
            delay = base_delay * (2 ** (attempt - 1))
            jitter = delay * 0.25 * random.uniform(-1, 1)
            wait = delay + jitter
            print(f"[Retry] Attempt {attempt}/{max_retries} failed: {e}. Retrying in {wait:.2f}s...")
            time.sleep(wait)
