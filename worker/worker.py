import json
from queue_layer.rabbitmq import consume_tasks
from api.retrieval import add_image, query_text

WORKER_ID = "worker-1"


def process_task(ch, method, properties, body):
    task = json.loads(body)

    print(f"[{WORKER_ID}] Received task: {task}", flush=True)

    try:
        if task["type"] == "text_query":
            results, embedding_shape = query_text(task["query"])
            print(f"[{WORKER_ID}] Completed text query: {task['query']}", flush=True)

        elif task["type"] == "image_upload":
            print(f"[{WORKER_ID}] Image task received (not fully wired yet)", flush=True)

        else:
            print(f"[{WORKER_ID}] Unknown task type: {task}", flush=True)

    except Exception as e:
        print(f"[{WORKER_ID}] Error processing task: {e}", flush=True)


if __name__ == "__main__":
    print(f"[{WORKER_ID}] Starting worker loop...", flush=True)
    consume_tasks(process_task)



    