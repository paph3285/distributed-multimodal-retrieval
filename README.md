# A Distributed Multimodal Retrieval System Using CLIP Embeddings

## Overview

This project implements a distributed system for multimodal retrieval using pretrained CLIP embeddings. The system allows users to submit either an image or a text query and retrieves the most relevant matches in a shared embedding space.

The primary goal of this project is not to train a new machine learning model, but to design and implement a scalable distributed system that supports multimodal AI workloads using asynchronous processing, modular components, and efficient similarity search. This project emphasizes system design and infrastructure for multimodal AI, rather than model training.

---

## System Functionality

The system supports two main workflows:

### 1. Image-to-Text Retrieval

- A user uploads an image
- The system generates an embedding using a pretrained CLIP model
- The embedding is compared to predefined text label embeddings
- The system returns the most relevant labels

### 2. Text-to-Image Retrieval

- A user submits a text query (e.g., "forest", "city")
- The system converts the query into an embedding
- The embedding is compared against stored image embeddings
- The system returns the most similar images

---

## Current Implementation (Prototype System)

The current implementation provides a fully functional end-to-end multimodal retrieval pipeline using a curated dataset, precomputed embeddings, and a modular API-based architecture.

### Key Components

- **FastAPI Backend**
  - Handles image uploads and text queries
  - Serves retrieval results, debug endpoints, and system metrics

- **CLIP Model (ViT-B/32)**
  - Generates 512-dimensional embeddings for both images and text
  - Enables cross-modal retrieval within a shared embedding space

- **FAISS Index**
  - Stores image embeddings in-memory
  - Performs efficient nearest neighbor search using cosine similarity

- **Curated Landscape Dataset**
  - Images organized using filename-based labels (e.g., forest_1.jpg)
  - Labels are automatically extracted using:
    ```python
    label = filename.split("_")[0]
    ```

---

## Retrieval Pipeline

### Dataset Initialization

- On startup, images are loaded from: `storage/curated_landscapes/`
- Labels are inferred from filenames
- Embeddings are precomputed at startup to enable low-latency retrieval
- FAISS index is built and stored in memory

### Text-to-Image Retrieval

- Query is encoded using CLIP
- FAISS returns top-K similar images
- Results include:
    * filename
    * label
    * similarity score
    * image URL

---

## System Architecture

This section outlines the target distributed architecture; the current prototype implements the FastAPI + CLIP + FAISS components locally. The system is designed as a distributed, asynchronous pipeline with the following components:

- **API (FastAPI)**: Handles user requests and orchestration
- **Message Queue (RabbitMQ) (planned)**: Enables asynchronous job distribution
- **Worker Nodes (PyTorch + CLIP) (planned)**: Perform embedding generation at scale
- **Vector Database (FAISS)**: Stores embeddings and performs similarity search
- **Relational Database (PostgreSQL) (planned)**: Tracks metadata and job status
- **Storage (Local / Object Storage)**: Stores uploaded and curated images
- **Docker**: Containerizes system components for reproducibility

---

## Key Design Decisions

- Use of **pretrained CLIP embeddings** (no model training required)
- Focus on **landscape image categories** for controlled evaluation
- Precomputation of embeddings for low-latency retrieval
- Implementation of an **asynchronous pipeline** using RabbitMQ
- Use of **FAISS for efficient similarity search**
- Modular design to support **future distributed scaling**
- Local-first deployment using **Docker Compose**

---

## Dataset

The system uses a curated dataset of landscape images with predefined labels such as:
- forest
- mountain
- beach
- city
- desert
- river

Images are stored locally and may be sourced from publicly available datasets such as RESISC45.

---

## Project Structure

```md
distributed-multimodal-retrieval/
├── api/
├── db/
├── docker/
├── docs/
├── queue_layer/
├── storage/
├── vector_store/
├── worker/
├── venv/
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
```
---

## Setup

The system is designed to run locally using Docker Compose.

Basic setup includes:
- Environment configuration (`.env`)
- Container startup (`docker-compose up`)
- API access via `http://localhost:8000`

---

## Example Usage

The system supports both text-to-image and image-to-text retrieval workflows through the FastAPI interface.

### Text-to-Image Retrieval

A user submits a text query such as 
```md 
"forest"
```

The system:

- Encodes the query using CLIP
- Searches the FAISS index for similar image embeddings
- Returns the top-K most relevant images

**Example Response (JSON):**

```md 
[{"filename": "forest_3.jpg", "label": "forest", "score": 0.92, "image_url": "http://localhost:8000/storage/forest_3.jpg"}, {"filename": "forest_7.jpg", "label": "forest", "score": 0.89, "image_url": "http://localhost:8000/storage/forest_7.jpg"}]
```

---

### Image-to-Text Retrieval

A user uploads an image file.

The system:

- Generates an image embedding using CLIP
- Compares it against predefined text label embeddings
- Returns the most relevant labels
**Example Output (JSON):**

```md
{"top_labels": [{"label": "mountain", "score": 0.87}, {"label": "forest", "score": 0.82}]}`
```

---

### Debug Endpoints

The system includes built-in endpoints for monitoring and debugging:

- `/debug/status/` → system metrics
- `/debug/images/` → indexed dataset
- `/debug/jobs/` → job tracking
- `/debug/queue/` → queue state


## Status

**Current State: Functional Local Prototype**
- End-to-end multimodal retrieval system is operational
- Supports both image upload and text query workflows
- FAISS index built and queried in real time
- Dataset preloaded with precomputed embeddings
- Debug and monitoring endpoints available

---

### Extended Implementation Details (Prototype System)

**System Execution (Local Prototype)**
The system is fully operational as a local prototype and extends the architecture with additional modular components and observability features.

The implementation includes:
- End-to-end request handling via FastAPI
- Real-time embedding generation using CLIP (ViT-B/32)
- FAISS-based similarity search over precomputed embeddings
- Simulated task queue layer for asynchronous workflow modeling
- System monitoring through debug endpoints

---

### Extended System Components

#### API Layer (`api/`)

- `main.py`  
  - Defines FastAPI routes and entrypoints
- `processing.py`  
  - Handles task orchestration between components
- `retrieval.py`  
  - Interfaces with CLIP and FAISS for embedding + search

#### Queue Layer (`queue_layer/`)

- `task_queue.py`
  - Simulates core behaviors of an asynchronous message queue, including:
    - task enqueue and dequeue operations  
    - queue depth monitoring  
    - worker assignment and task distribution  
    - queue wait time and processing latency measurement  

#### Vector Store (`vector_store/`)

- `faiss_store.py`
  - Responsible for:
    - FAISS index creation
    - embedding storage
    - nearest neighbor retrieval

---

### Debug and Monitoring Endpoints

- `/debug/status/` → system metrics  
- `/debug/images/` → indexed dataset  
- `/debug/jobs/` → job tracking  
- `/debug/queue/` → queue state  

---

### Runtime System Characteristics

- Total images indexed: 30  
- Embedding dimension: 512  
- FAISS index initialized and active  
- Worker roles simulated:
  - image processing worker  
  - text query worker  
- Average queue wait time: ~100 ms  
- Successful execution of:
  - image upload tasks  
  - text query tasks  

---

### Implementation Notes

- Embeddings are precomputed at startup for low-latency retrieval  
- Labels are extracted using:
  ```python
  label = filename.split("_")[0]
  ```

---

## Future Directions

- Integrate RabbitMQ for true asynchronous processing
- Add worker services for distributed embedding generation
- Introduce PostgreSQL for metadata and job tracking
- Deploy system using Docker + Kubernetes (GKE)

