import pika
import json

RABBITMQ_HOST = "rabbitmq"
QUEUE_NAME = "task_queue"


def get_connection():
    return pika.BlockingConnection(
        pika.ConnectionParameters(host=RABBITMQ_HOST)
    )


def publish_task(task: dict):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_publish(
        exchange="",
        routing_key=QUEUE_NAME,
        body=json.dumps(task),
    )

    connection.close()


def consume_tasks(callback):
    connection = get_connection()
    channel = connection.channel()

    channel.queue_declare(queue=QUEUE_NAME)

    channel.basic_consume(
        queue=QUEUE_NAME,
        on_message_callback=callback,
        auto_ack=True,
    )

    print("[RabbitMQ] Waiting for tasks...", flush=True)
    channel.start_consuming()
