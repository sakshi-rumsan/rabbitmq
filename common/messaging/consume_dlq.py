"""
Dead Letter Queue (DLQ) consumer: listens to dead letter queue and stores failed messages in a JSON file for inspection.
"""
import json
from common.messaging.connection import get_connection
from common.messaging.queues import declare_queue
from common.messaging.exchanges import declare_exchange

EXCHANGE_NAME = "dlq.events"
QUEUE_NAME = "dlq.queue"
DLQ_JSON_PATH = "data/dlq_events.json"

def callback(ch, method, properties, body):
    try:
        event = json.loads(body)
    except Exception:
        event = {"raw": body.decode("utf-8", errors="replace")}
    print("[DLQ] Received dead letter event:", event)
    try:
        with open(DLQ_JSON_PATH, "r+") as file:
            events = json.load(file)
            events.append(event)
            file.seek(0)
            json.dump(events, file, indent=4)
    except FileNotFoundError:
        with open(DLQ_JSON_PATH, "w") as file:
            json.dump([event], file, indent=4)

def main():
    connection = get_connection()
    channel = connection.channel()
    declare_exchange(EXCHANGE_NAME, exchange_type="fanout")
    declare_queue(QUEUE_NAME)
    channel.queue_bind(exchange=EXCHANGE_NAME, queue=QUEUE_NAME)
    channel.basic_consume(queue=QUEUE_NAME, on_message_callback=callback, auto_ack=True)
    print(f"[DLQ] Waiting for dead letter events...")
    channel.start_consuming()

if __name__ == "__main__":
    main()
