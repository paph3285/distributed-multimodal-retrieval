# Implementation

## Phase 1. System Initialization

On startup, the system initializes core components required for retrieval and processing.

This includes:

- Loading the curated image dataset into memory
- Generating CLIP embeddings for each image
- Normalizing embeddings for similarity comparison
- Building the FAISS index for efficient nearest neighbor search
- Initializing the PostgreSQL database for job tracking

This process is triggered by the FastAPI startup event:

```python
@app.on_event("startup")
def startup_event():
    load_curated_dataset()
    initialize_database()
```

By performing these steps at startup, the system ensures that all retrieval operations can be executed immediately without additional preprocessing delays.

---

## Phase 2. Image Upload Pipeline

The image upload pipeline handles ingestion, embedding generation, and indexing of new images into the system.

### API Ingestion

Images are uploaded through the `/upload_image/` endpoint. The API saves the file to the upload directory using a streaming write to avoid memory issues:

```python
with open(file_path, "wb") as f:
    shutil.copyfileobj(file.file, f)
```

### Job Creation and Queue Simulation

A unique job ID is generated and a job record is created to track processing:

* Job status initialized as "started"
* Task is added to the queue
* Queue simulates asynchronous processing

```python
job_id = str(uuid.uuid4())
enqueue_task("image_upload", filename)
```

### Worker Processing

The system simulates a worker picking up the task:

* Task is dequeued
* Processing delay is introduced (asyncio.sleep)
* Worker ID is assigned

```python
await asyncio.sleep(0.1)
dequeue_task(worker_id="worker-image-1")
```

### Embedding Generation

The image is processed using CLIP:

* Image is preprocessed
* Passed through the CLIP encoder
* Feature vector is extracted

```python
image_features = model.encode_image(image)
```

### Embedding Normalization

The embedding is normalized to ensure consistent similarity comparisons:

```python
embedding = embedding / np.linalg.norm(embedding)
```

This step is critical because FAISS similarity search assumes normalized vectors when using distance-based comparisons.

### Label Assignment

A label is assigned using a simple filename-based heuristic:

```python
assigned_label = filename.split("_")[0]
```

This provides a lightweight way to associate semantic meaning without requiring model classification.

### Vector Store Update

The new embedding is added to the in-memory database, and the FAISS index is rebuilt:

```python
FAISS_INDEX = rebuild_faiss_index(IMAGE_DB, FAISS_DIM)
```

### Job Completion and Response

Once processing is complete:

* Job status is updated
* Duration is recorded
* Response is returned to the user

```python
return {
    "assigned_label": assigned_label,
    "image_embedding_shape": image_embedding_shape
}
```

This pipeline ensures that newly uploaded images are immediately available for retrieval.

---

## Phase 3. Text Query Pipeline

The text query pipeline handles user search requests and returns the most relevant images from the FAISS index.

### Query Request

Text queries are submitted through the `/text-query/` endpoint:

```python
@app.get("/text-query/")
async def text_query(query: str):
```

The query is passed from the API layer into the processing layer.

### Job Tracking and Queue Publishing

A job record is created for the query, and the task is sent through the queue flow:

```python
job_id = str(uuid.uuid4())

publish_task({
    "type": "text_query",
    "query": query
})

enqueue_task("text_query", query)
```

This allows the system to track the request as a processing job.

### Cache Check
Before running CLIP inference, the system checks whether the same query has already been processed:
```python
if query in QUERY_CACHE:
    CACHE_HITS += 1
    results, embedding_shape = QUERY_CACHE[query]
```
If the query is cached, the previous results are reused.

### Text Embedding Generation

If the query is not cached, it is tokenized and encoded using CLIP:

```python
text_tokens = clip.tokenize([query]).to(device)

with torch.no_grad():
    text_features = model.encode_text(text_tokens)
```

The resulting text embedding is normalized before search.

### FAISS Search

The normalized text embedding is passed into FAISS to retrieve the closest image embeddings:

```python
distances, indices = search_faiss_index(
    FAISS_INDEX,
    text_embedding,
    top_k
)
```

The number of returned results is capped by the available number of indexed images.

### Result Scoring

For each retrieved image, the system computes:

* FAISS distance
* similarity score
* optional label boost
* final score

```python
similarity_score = 1 / (1 + distance)
label_boost = 0.05 if img["label"].lower() == query.lower() else 0.0
final_score = similarity_score + label_boost
```

The label boost helps exact category matches appear slightly higher in the final ranking.

### Result Formatting

Each result includes metadata used by the API response:

```python
{
    "rank": rank + 1,
    "filename": img["filename"],
    "label": img["label"],
    "distance": round(distance, 4),
    "similarity_score": round(similarity_score, 4),
    "final_score": round(final_score, 4),
    "image_url": image_url
}
```

Results are sorted by final_score before being returned.

### Job Completion

After retrieval is complete:

* The job status is updated
* Query results are cached
* Processing duration is recorded
* Job results are saved to PostgreSQL

This pipeline allows repeated queries to run faster while still supporting real-time retrieval for new text inputs.

---

## Phase 4. FAISS Index and Vector Store

The vector store layer manages how image embeddings are stored and searched during retrieval.

### Index Construction

Image embeddings are stored in memory as part of `IMAGE_DB`. Each record includes:

- filename
- label
- embedding vector
- image source

After embeddings are generated, the FAISS index is rebuilt from the current image database:

```python
FAISS_INDEX = rebuild_faiss_index(IMAGE_DB, FAISS_DIM)
```

### Embedding Format

CLIP produces 512-dimensional embeddings, so the FAISS index is configured using:

```python
FAISS_DIM = 512
```

Before being added to the index, embeddings are normalized so distance comparisons are consistent.

### Search Behavior

During retrieval, the normalized query embedding is compared against indexed image embeddings:

```python
distances, indices = search_faiss_index(
    FAISS_INDEX,
    text_embedding,
    top_k
)
```

FAISS returns both distances and indices. The indices are used to look up the matching image records in IMAGE_DB, while the distances are converted into similarity scores for ranking.

### Runtime Status

The vector store exposes status information through the debug system, including whether the FAISS index is initialized and how many vectors are currently indexed.

This helps confirm that retrieval is using the active in-memory index rather than relying on static files alone.

---

## Phase 5. Queue and Worker Simulation

The system includes a simulated task queue and worker model to represent asynchronous processing behavior typically found in distributed systems.

### Task Queue Integration

When a request is received, a task is created and pushed to the queue:

```python
enqueue_task("image_upload", filename)
enqueue_task("text_query", query)
```

For text queries, tasks are also published to RabbitMQ:

```python
publish_task({
    "type": "text_query",
    "query": query
})
```

This separation allows the system to simulate message-based communication between services.

### Queue Behavior

The queue maintains:

* Pending tasks
* Processed tasks
* Queue depth history
* Per-task wait times

Tasks are processed in FIFO order.

### Worker Simulation

Workers are simulated within the processing layer using controlled delays:

```python
await asyncio.sleep(0.1)
dequeue_task(worker_id="worker-text-1")
```

Each task is assigned a worker ID to track which worker processed it.

### Queue Metrics

The system tracks queue-related performance metrics:

* Average queue wait time
* Minimum and maximum wait times
* Queue depth over time
* Number of processed vs queued tasks

These metrics are exposed through the /debug/status/ endpoint.

### Worker Summary

Processed tasks are grouped by worker ID to provide a summary of workload distribution:

```python
worker_summary[worker_id] = worker_summary.get(worker_id, 0) + 1
```

### Design Rationale

Although the system runs synchronously, this simulation models how a real distributed system would:

* Decouple request handling from processing
* Support horizontal scaling via multiple workers
* Use message queues for task coordination

This design allows the system to demonstrate distributed architecture patterns without requiring full deployment infrastructure.

---

## Phase 6. Caching and Performance Optimization

The system includes a lightweight caching layer to improve performance for repeated text queries.

### Query Cache

A dictionary-based cache is used to store previously computed query results:

```python
QUERY_CACHE = {}
```

Each query string is used as a key, with the corresponding retrieval results stored as the value.

### Cache Lookup

Before performing CLIP inference and FAISS search, the system checks whether the query already exists in the cache:

```pyython
QUERY_CACHE[query] = (results, embedding_shape)
CACHE_MISSES += 1
```

### Performance Tracking

The system tracks:

* Total cache size
* Cache hits
* Cache misses

These metrics are exposed through the /debug/status/ endpoint and provide insight into how often repeated queries are reused.

### Design Rationale

Caching reduces redundant computation by avoiding repeated CLIP encoding and FAISS search for identical queries.

This is especially useful in retrieval systems where common queries are likely to occur multiple times.

---

## Phase 7. Job Tracking and Metrics

The system maintains detailed job tracking and performance metrics to monitor how tasks are processed over time.

### Job History

Each request (image upload or text query) is recorded as a job entry:

```python
JOB_HISTORY = []
```
Each job record includes:

* job ID
* task type (image_upload or text_query)
* input value
* status (started, completed, failed)
* result metadata
* execution duration

Jobs are appended at the start of processing and updated as the task progresses.

### Job Lifecycle

A job transitions through the following states:

1. Started — job is created and queued
2. Completed — processing finishes successfully
3. Failed — an error occurs during execution

Duration is recorded using high-resolution timing:

```python
start_time = time.perf_counter()
duration_ms = (time.perf_counter() - start_time) * 1000
```

### Metrics Collection

The system aggregates metrics across all jobs, including:

* Total number of jobs
* Completed and failed job counts
* Average job duration
* Average upload duration
* Average query duration

These metrics provide a summary of system performance over time.

### Queue Metrics Integration

Job tracking is combined with queue metrics to provide additional insights:

* Average queue wait time
* Minimum and maximum wait times
* Queue depth history
* Worker utilization

This allows the system to measure not just processing time, but also time spent waiting in the queue.

#### Worker Performance Tracking

Jobs are grouped by worker ID to analyze workload distribution:

```python
worker_summary[worker_id] = worker_summary.get(worker_id, 0) + 1
```

The system also computes average processing time per worker to simulate performance differences across distributed workers.

### Database Integration

Job results are also persisted in PostgreSQL for durability:

```python
save_job_result(
    task_type="text_query",
    input_value=query,
    status="completed",
    result_text=f"{len(results)} results returned"
)
```

Recent database entries are included in debug responses to validate persistence.

### Debug Endpoints

All metrics are exposed through debug endpoints, particularly:

* /debug/status/ → system-wide metrics
* /debug/jobs/ → full job history
* /debug/db/jobs/ → database records

These endpoints allow real-time inspection of system behavior during execution.

### Design Rationale

Tracking jobs and metrics provides visibility into system performance and reliability.

This is essential in distributed systems where tasks are processed asynchronously and failures must be monitored and debugged.

---

## Phase 8. Design Decisions and Limitations

### Design Decisions

- **Pretrained CLIP (ViT-B/32)**  
  Used to enable a shared embedding space for both images and text without additional training.

- **FAISS for similarity search**  
  Chosen for efficient nearest neighbor retrieval over high-dimensional embeddings.

- **In-memory image database + dynamic index rebuild**  
  Simplifies integration with FAISS and ensures new uploads are immediately searchable.

- **Simulated queue and workers**  
  Allows demonstration of asynchronous, distributed patterns without full infrastructure deployment.

- **Lightweight scoring adjustment (label boost)**  
  Improves ranking interpretability by slightly prioritizing exact label matches.

- **Query caching**  
  Reduces repeated computation for common queries and improves response time.


### Limitations

- **No true asynchronous workers**  
  Task execution is simulated using delays rather than separate worker processes.

- **FAISS index rebuild on each upload**  
  Not optimized for large-scale datasets or frequent updates.

- **Simple label assignment**  
  Labels are derived from filenames rather than predicted by a model.

- **Limited dataset size**  
  Retrieval quality is constrained by the small curated dataset.

- **No authentication or access control**  
  The API is open and intended for local development and testing only.

### Future Improvements

- Introduce real worker services with RabbitMQ consumers  
- Replace FAISS with a scalable vector database (e.g., Milvus or pgvector)  
- Implement incremental index updates instead of full rebuilds  
- Add evaluation metrics such as Recall@K  
- Expand dataset and support batch query processing  
- Deploy system using Docker Compose and Kubernetes (GKE)