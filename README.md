# A Distributed Multimodal Retrieval System Using CLIP Embeddings

## Overview

This project implements a distributed system for multimodal retrieval using pretrained CLIP embeddings. The system allows users to submit either an image or a text query and retrieves the most relevant matches in a shared embedding space.

The primary goal of this project is not to train a new machine learning model, but to design and implement a scalable distributed system that supports multimodal AI workloads using asynchronous processing and modular components.

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
The current implementation focuses on a working end-to-end multimodal retrieval pipeline using a curated dataset and a modular API design.

### Key Components
- **FastAPI Backend**
  - Handles image uploads and text queries
  - Serves retrieval results and debug endpoints

- **CLIP Model (ViT-B/32)**
  - Generates 512-dimensional embeddings for both images and text
  - Enables cross-modal retrieval in a shared embedding space

- **FAISS Index**
  - Stores image embeddings
  - Performs efficient nearest neighbor search for retrieval

- **Curated Landscape Dataset**
  - Images organized using filename-based labels (e.g., `forest_1.jpg`)
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
- FAISS index is built from image embeddings

### Text-to-Image Retrieval
- Query is encoded using CLIP
- FAISS returns top-K similar images
- Results include filename, label, distance, and image URL

---

## System Architecture

This section outlines the target distributed architecture; the current prototype implements the FastAPI + CLIP + FAISS components locally. This system is designed as a distributed, asynchronous pipeline with the following components:

- **API (FastAPI)**: Handles user requests and system coordination
- **Message Queue (RabbitMQ)**: Manages asynchronous job distribution
- **Worker Nodes (PyTorch + CLIP)**: Generate embeddings for images
- **Vector Database (FAISS)**: Stores embeddings and performs similarity search
- **Relational Database (PostgreSQL)**: Tracks metadata and job status
- **Storage (Local)**: Stores uploaded images
- **Docker**: Containerizes all system components

---

## Key Design Decisions

- Use of **pretrained CLIP embeddings** (no model training required)
- Focus on **landscape image categories** for controlled evaluation
- Implementation of an **asynchronous pipeline** using RabbitMQ
- Use of **FAISS for efficient similarity search**
- Local-first deployment using **Docker Compose**

---

## Dataset

The system uses a small curated dataset of landscape images with predefined labels such as:
- forest
- mountain
- beach
- city
- desert
- river

Images are stored locally and may be sourced from publicly available datasets such as RESISC45.

---

## Project Structure

```
distributed-multimodal-retrieval/
├── api/
├── worker/
├── queue/
├── db/
├── vector_store/
├── storage/
├── docker/
├── scripts/
├── tests/
├── data/
├── docs/
├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
├── requirements.txt 
```
---

## Setup

This project will be run locally using Docker Compose. Setup instructions will be added as each component is implemented.

---

## Status

---

## Extended Implementation Details (Prototype System)

### System Execution (Local Prototype)

The current system is fully operational as a local prototype and extends the architecture described above with additional modular components and instrumentation.

The implementation includes:

- End-to-end image and text query handling through FastAPI
- Real-time embedding generation using pretrained CLIP (ViT-B/32)
- FAISS-based similarity search over a precomputed embedding index
- A simulated task queue layer to model asynchronous processing behavior
- Worker tracking and performance monitoring for system observability

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
  - Simulates:
    - task enqueue/dequeue operations
    - queue depth tracking
    - worker assignment
    - queue wait time measurement

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