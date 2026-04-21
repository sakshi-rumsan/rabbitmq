from .connection import get_connection


def setup_retry_infrastructure(
    work_queue: str,
    exchange: str,
    routing_key: str,
    retry_ttl_ms: int = 5000,
) -> None:
    """
    Declare retry and DLQ infrastructure for a work queue.

    Message flow on nack(requeue=False):
        work_queue --> retry_exchange --> retry_queue (waits TTL ms)
                                               |
                                       (TTL expires → back to work_queue)

    After RabbitMQ's internal per-queue x-delivery-count exceeds the
    consumer's own threshold, the consumer should nack without requeue and
    the message lands in dlq.queue for manual inspection.

    Args:
        work_queue:    Name of the queue that processes messages normally.
        exchange:      Exchange that routes messages to work_queue.
        routing_key:   Routing key used between exchange and work_queue.
        retry_ttl_ms:  How long (ms) a nacked message waits before retry.
    """
    connection = get_connection()
    channel = connection.channel()

    retry_exchange = f"{work_queue}.retry.exchange"
    retry_queue = f"{work_queue}.retry"
    dlq_exchange = "dlq.events"
    dlq_queue = "dlq.queue"

    # DLQ infrastructure
    channel.exchange_declare(exchange=dlq_exchange, exchange_type="fanout", durable=True)
    channel.queue_declare(queue=dlq_queue, durable=True)
    channel.queue_bind(exchange=dlq_exchange, queue=dlq_queue)

    # Retry exchange (direct so routing key is preserved)
    channel.exchange_declare(exchange=retry_exchange, exchange_type="direct", durable=True)

    # Retry queue: messages wait here for TTL, then fall back to work_queue
    channel.queue_declare(
        queue=retry_queue,
        durable=True,
        arguments={
            "x-message-ttl": retry_ttl_ms,
            "x-dead-letter-exchange": exchange,
            "x-dead-letter-routing-key": routing_key,
        },
    )
    channel.queue_bind(exchange=retry_exchange, queue=retry_queue, routing_key=routing_key)

    # Work queue: failed messages go to retry exchange
    channel.queue_declare(
        queue=work_queue,
        durable=True,
        arguments={
            "x-dead-letter-exchange": retry_exchange,
            "x-dead-letter-routing-key": routing_key,
        },
    )

    connection.close()
    print(f"[RetryInfra] Declared retry infrastructure for queue '{work_queue}' (TTL={retry_ttl_ms}ms)")
