from .connection import get_connection


def declare_exchange(
    exchange_name: str,
    exchange_type: str = "direct",
    durable: bool = True,
    channel=None,
) -> None:
    if channel is not None:
        channel.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)
        return
    connection = get_connection()
    ch = connection.channel()
    ch.exchange_declare(exchange=exchange_name, exchange_type=exchange_type, durable=durable)
    connection.close()
