from .connection import get_connection


def declare_queue(queue_name: str, durable: bool = True) -> None:
    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=durable)
    connection.close()