# RabbitMQ exchanges setup
from .connection import get_connection

def declare_exchange(exchange_name, exchange_type="direct"):
    connection = get_connection()
    channel = connection.channel()
    channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type)
    connection.close()