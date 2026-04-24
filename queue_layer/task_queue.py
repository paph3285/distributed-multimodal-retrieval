import uuid
import time

TASK_QUEUE = []
PROCESSED_TASKS = []
QUEUE_DEPTH_HISTORY = []


def enqueue_task(task_type, input_value):
    task_id = str(uuid.uuid4())

    task_record = {
        "task_id": task_id,
        "task_type": task_type,
        "input": input_value,
        "status": "queued",
        "enqueued_at": time.perf_counter()
    }

    TASK_QUEUE.append(task_record)

    QUEUE_DEPTH_HISTORY.append({
        "event": "enqueue",
        "task_type": task_type,
        "queued_count": len(TASK_QUEUE),
        "timestamp": time.perf_counter()
    })

    return task_record


def dequeue_task(worker_id="worker-1"):
    if len(TASK_QUEUE) == 0:
        return None

    task_record = TASK_QUEUE.pop(0)
    task_record["status"] = "dequeued"
    task_record["worker_id"] = worker_id
    task_record["dequeued_at"] = time.perf_counter()
    task_record["queue_wait_ms"] = round(
        (task_record["dequeued_at"] - task_record["enqueued_at"]) * 1000,
        2
    )
    PROCESSED_TASKS.append(task_record)

    QUEUE_DEPTH_HISTORY.append({
        "event": "dequeue",
        "task_type": task_record.get("task_type"),
        "queued_count": len(TASK_QUEUE),
        "timestamp": time.perf_counter()
    })

    return task_record


def get_queue_depth_history():
    return QUEUE_DEPTH_HISTORY
    

def get_queue_status():
    return {
        "queued_task_count": len(TASK_QUEUE),
        "processed_task_count": len(PROCESSED_TASKS),
        "queue_depth_history_count": len(QUEUE_DEPTH_HISTORY)
    }

def get_all_tasks():
    return {
        "queued_tasks": TASK_QUEUE,
        "processed_tasks": PROCESSED_TASKS
    }

{
  "all_tasks": {
    "queued_tasks": [],
    "processed_tasks": [
      {
        "task_id": "2e3bb990-438f-4192-bd03-cceea0462803",
        "task_type": "text_query",
        "input": "forest",
        "status": "dequeued"
      }
    ]
  },
  "queue_status": {
    "queued_task_count": 0,
    "processed_task_count": 1
  }
}