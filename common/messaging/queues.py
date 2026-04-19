# RabbitMQ queues setup
from .connection import get_connection

def declare_queue(queue_name):
    connection = get_connection()
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)
    connection.close()