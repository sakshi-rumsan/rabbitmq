from .connection import get_connection


def declare_queue(queue_name: str, durable: bool = True, channel=None, arguments: dict = None) -> None:
    if channel is not None:
        channel.queue_declare(queue=queue_name, durable=durable, arguments=arguments)
        return
    connection = get_connection()
    ch = connection.channel()
    ch.queue_declare(queue=queue_name, durable=durable, arguments=arguments)
    connection.close()
