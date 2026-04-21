"""
Dead Letter Queue (DLQ) consumer: listens to dead letter queue and stores failed messages in a JSON file for inspection.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange
from common.utils.json_store import append_to_json_file

EXCHANGE_NAME = "dlq.events"
QUEUE_NAME = "dlq.queue"
DLQ_JSON_PATH = "data/dlq_events.json"

def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
    except Exception:
        event = {"raw": body.decode("utf-8", errors="replace")}
    print("[DLQ] Received dead letter event:", event)
    append_to_json_file(DLQ_JSON_PATH, event)

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout", channel=channel)
    declare_queue(QUEUE_NAME, channel=channel)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[DLQ] Waiting for dead letter events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
