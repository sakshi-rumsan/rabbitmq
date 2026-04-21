import pika
from .connection import get_connection


def publish_message(exchange: str, routing_key: str, message: str) -> None:
    connection = get_connection()
    channel = connection.channel()
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make message persistent
            content_type="application/json",
        ),
    )
    connection.close()