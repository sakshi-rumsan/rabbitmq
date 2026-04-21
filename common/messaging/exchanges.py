from .connection import get_connection


def declare_exchange(exchange_name: str, exchange_type: str = "direct", durable: bool = True) -> None:
    connection = get_connection()
    channel = connection.channel()
    channel.exchange_declare(
        exchange=exchange_name,
        exchange_type=exchange_type,
        durable=durable,
    )
    connection.close()