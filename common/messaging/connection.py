# RabbitMQ connection setup
import pika

def get_connection():
    return pika.BlockingConnection(pika.ConnectionParameters("localhost"))