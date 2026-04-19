# RabbitMQ producer
from .connection import get_connection

def publish_message(exchange, routing_key, message):
    connection = get_connection()
    channel = connection.channel()
    channel.basic_publish(exchange=exchange, routing_key=routing_key, body=message)
    connection.close()