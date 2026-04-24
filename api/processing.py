import uuid
import asyncio
import time
from api.retrieval import add_image, query_text, get_system_status
from db.postgres_helper import save_job_result, get_job_results
from queue_layer.rabbitmq import publish_task
from queue_layer.task_queue import (
    enqueue_task,
    dequeue_task,
    get_all_tasks,
    get_queue_status,
    get_queue_depth_history
)


JOB_HISTORY = []
QUERY_CACHE = {}
CACHE_HITS = 0
CACHE_MISSES = 0


async def process_image_upload(file_path, filename):
    start_time = time.perf_counter()
    job_id = str(uuid.uuid4())

    job_record = {
        "job_id": job_id,
        "task_type": "image_upload",
        "input": filename,
        "status": "started"
    }
    JOB_HISTORY.append(job_record)

    enqueue_task("image_upload", filename)

    try:
        await asyncio.sleep(0.1)
        dequeue_task(worker_id="worker-image-1")

        assigned_label, image_embedding_shape = add_image(file_path, filename)

        job_record["status"] = "completed"
        job_record["result"] = {
            "assigned_label": assigned_label,
            "image_embedding_shape": image_embedding_shape
        }

        return assigned_label, image_embedding_shape

    except Exception as e:
        job_record["status"] = "failed"
        job_record["error"] = str(e)
        raise

    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        job_record["duration_ms"] = round(duration_ms, 2)



async def process_text_query(query):
    global CACHE_HITS, CACHE_MISSES
    start_time = time.perf_counter()
    job_id = str(uuid.uuid4())

    job_record = {
        "job_id": job_id,
        "task_type": "text_query",
        "input": query,
        "status": "started"
    }
    JOB_HISTORY.append(job_record)

    task = {
        "type": "text_query",
        "query": query
    }
    publish_task(task)

    enqueue_task("text_query", query)

    try:
        await asyncio.sleep(0.1)
        dequeue_task(worker_id="worker-text-1")

        if query in QUERY_CACHE:
            CACHE_HITS += 1
            results, embedding_shape = QUERY_CACHE[query]
        else:
            CACHE_MISSES += 1
            results, embedding_shape = query_text(query)
            QUERY_CACHE[query] = (results, embedding_shape)

        job_record["status"] = "completed"
        job_record["result"] = {
            "result_count": len(results),
            "embedding_shape": embedding_shape
        }

        save_job_result(
            task_type="text_query",
            input_value=query,
            status="completed",
            result_text=f"{len(results)} results returned"
        )

        return results, embedding_shape

    except Exception as e:
        job_record["status"] = "failed"
        job_record["error"] = str(e)

        save_job_result(
            task_type="text_query",
            input_value=query,
            status="failed",
            result_text=str(e)
        )

        raise

    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        job_record["duration_ms"] = round(duration_ms, 2)



def get_job_history():
    return JOB_HISTORY


def get_processing_status():
    last_job_type = JOB_HISTORY[-1]["task_type"] if JOB_HISTORY else None
    completed_jobs = sum(1 for job in JOB_HISTORY if job["status"] == "completed")
    failed_jobs = sum(1 for job in JOB_HISTORY if job["status"] == "failed")

    all_durations = [job["duration_ms"] for job in JOB_HISTORY if "duration_ms" in job]
    upload_durations = [
        job["duration_ms"]
        for job in JOB_HISTORY
        if job["task_type"] == "image_upload" and "duration_ms" in job
    ]
    query_durations = [
        job["duration_ms"]
        for job in JOB_HISTORY
        if job["task_type"] == "text_query" and "duration_ms" in job
    ]

    average_job_duration_ms = round(sum(all_durations) / len(all_durations), 2) if all_durations else 0
    average_upload_duration_ms = round(sum(upload_durations) / len(upload_durations), 2) if upload_durations else 0
    average_query_duration_ms = round(sum(query_durations) / len(query_durations), 2) if query_durations else 0

    all_tasks = get_all_tasks()
    processed_tasks = all_tasks["processed_tasks"]
    queued_tasks = all_tasks["queued_tasks"]
    queue_depth_history = get_queue_depth_history()

    last_queue_event = None
    if queue_depth_history:
        last_queue_event = queue_depth_history[-1]  

    queued_task_preview = [
        {
            "task_type": task.get("task_type"),
            "input": task.get("input")
        }
        for task in queued_tasks
    ]

    queue_wait_times = [
        task["queue_wait_ms"]
        for task in processed_tasks
        if "queue_wait_ms" in task
    ]

    average_queue_wait_ms = round(
        sum(queue_wait_times) / len(queue_wait_times), 2
    ) if queue_wait_times else 0

    min_queue_wait_ms = min(queue_wait_times) if queue_wait_times else 0
    max_queue_wait_ms = max(queue_wait_times) if queue_wait_times else 0

    worker_summary = {}
    for task in processed_tasks:
        worker_id = task.get("worker_id")
        if worker_id:
            worker_summary[worker_id] = worker_summary.get(worker_id, 0) + 1

    task_type_summary = {}
    for task in processed_tasks:
        task_type = task.get("task_type")
        if task_type:
            task_type_summary[task_type] = task_type_summary.get(task_type, 0) + 1

    worker_timing_totals = {}
    worker_timing_counts = {}

    for job in JOB_HISTORY:

        task_type = job.get("task_type")

        duration_ms = job.get("duration_ms")

        if task_type == "image_upload":

            worker_id = "worker-image-1"

        elif task_type == "text_query":

            worker_id = "worker-text-1"

        else:
            worker_id = None
        if worker_id and duration_ms is not None:
            worker_timing_totals[worker_id] = worker_timing_totals.get(worker_id, 0) + duration_ms
            worker_timing_counts[worker_id] = worker_timing_counts.get(worker_id, 0) + 1

    worker_timing_summary = {
        worker_id: round(worker_timing_totals[worker_id] / worker_timing_counts[worker_id], 2)
        for worker_id in worker_timing_totals

    }


    last_processed_task = None
    if processed_tasks:
        latest_task = processed_tasks[-1]
        last_processed_task = {
            "task_type": latest_task.get("task_type"),
            "input": latest_task.get("input"),
            "worker_id": latest_task.get("worker_id"),
            "queue_wait_ms": latest_task.get("queue_wait_ms")
        }

    total_image_uploads_processed = task_type_summary.get("image_upload", 0)
    total_text_queries_processed = task_type_summary.get("text_query", 0)
    status_timestamp = time.perf_counter()

    db_results = get_job_results()
    recent_db_results = db_results[:5]

    return {
        "status_timestamp": status_timestamp,
        **get_system_status(),
        **get_queue_status(),
        "job_count": len(JOB_HISTORY),
        "completed_job_count": completed_jobs,
        "failed_job_count": failed_jobs,
        "last_job_type": last_job_type,
        "average_job_duration_ms": average_job_duration_ms,
        "average_upload_duration_ms": average_upload_duration_ms,
        "average_query_duration_ms": average_query_duration_ms,
        "average_queue_wait_ms": average_queue_wait_ms,
        "min_queue_wait_ms": min_queue_wait_ms,
        "max_queue_wait_ms": max_queue_wait_ms,
        "worker_summary": worker_summary,
        "task_type_summary": task_type_summary,
        "worker_timing_summary": worker_timing_summary,
        "total_image_uploads_processed": total_image_uploads_processed,
        "total_text_queries_processed": total_text_queries_processed,
        "last_processed_task": last_processed_task,
        "queued_task_preview": queued_task_preview,
        "last_queue_event": last_queue_event,
        "cache_size": len(QUERY_CACHE),
        "cache_hits": CACHE_HITS,
        "cache_misses": CACHE_MISSES,
        "db_total_records": len(db_results),
        "recent_db_results": recent_db_results,
    }


def get_queue_debug_info():
    return {
        "all_tasks": get_all_tasks(),
        "queue_status": get_queue_status(),
        "queue_depth_history": get_queue_depth_history()
    }   

def get_architecture_summary():
    return {
        "system_name": "Distributed Multimodal Retrieval System (GeoCLIP)",
        "current_implementation": {
            "api": "FastAPI service handling image uploads, text queries, and debug endpoints",
            "processing_layer": "Coordinates upload/query workflows, simulated queue behavior, caching, and job metrics",
            "queue_layer": "Simulates asynchronous task enqueue/dequeue behavior and worker assignment",
            "database": "PostgreSQL helper layer used for job result tracking",
            "vector_store": "FAISS index used for similarity search",
            "embedding_model": "Pretrained CLIP model used for image and text embeddings"
        },
        "features": [
            "Image-to-text retrieval",
            "Text-to-image retrieval",
            "Simulated asynchronous task queue",
            "Query caching layer",
            "Job tracking and runtime metrics",
            "System health and debug endpoints"
        ],
        "future_distributed_components": [
            "RabbitMQ message broker for true asynchronous job distribution",
            "Dedicated worker services for distributed embedding generation",
            "Expanded PostgreSQL metadata and job tracking",
            "Docker Compose / Kubernetes deployment"
        ]
    }