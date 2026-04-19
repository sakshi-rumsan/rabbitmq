# RabbitMQ consumer
from .connection import get_connection

def consume_messages(queue, callback):
    connection = get_connection()
    channel = connection.channel()
    channel.basic_consume(queue=queue, on_message_callback=callback, auto_ack=True)
    channel.start_consuming()