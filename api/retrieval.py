import os
import numpy as np
import torch, clip
from PIL import Image

from vector_store.faiss_store import (
    rebuild_faiss_index,
    search_faiss_index,
    get_faiss_status
)


# Retrieval layer: dataset loading, embedding generation, ranking


# Constants
UPLOAD_DIR = "storage/uploads"
CURATED_DIR = "storage/curated_landscapes"
FAISS_DIM = 512

# State
IMAGE_DB = []
FAISS_INDEX = None

# Setup
os.makedirs(UPLOAD_DIR, exist_ok=True)
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)


def normalize_vector(vec):
    vec = np.array(vec)
    return vec / np.linalg.norm(vec)



def add_image(file_path, filename):
    for img in IMAGE_DB:
        if img["filename"] == filename:
            image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)
            with torch.no_grad():
                image_features = model.encode_image(image)
            return img["label"], list(image_features.shape)

    image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)

    with torch.no_grad():
        image_features = model.encode_image(image)

    assigned_label = filename.split("_")[0]

    image_embedding = image_features.cpu().numpy()[0]
    image_embedding = normalize_vector(image_embedding)

    IMAGE_DB.append({
        "filename": filename,
        "label": assigned_label,
        "embedding": image_embedding.tolist(),
        "source": "uploaded"
    })

    global FAISS_INDEX
    FAISS_INDEX = rebuild_faiss_index(IMAGE_DB, FAISS_DIM)

    return assigned_label, list(image_features.shape)

def load_curated_dataset():
    global IMAGE_DB

    IMAGE_DB.clear()

    for filename in os.listdir(CURATED_DIR):
        if filename.lower().endswith((".jpg", ".png", ".jpeg")):
            file_path = os.path.join(CURATED_DIR, filename)

            image = preprocess(Image.open(file_path)).unsqueeze(0).to(device)

            with torch.no_grad():
                image_features = model.encode_image(image)

            label = filename.split("_")[0]

            image_embedding = image_features.cpu().numpy()[0]
            image_embedding = normalize_vector(image_embedding)

            IMAGE_DB.append({
                "filename": filename,
                "label": label,
                "embedding": image_embedding.tolist(),
                "source": "curated"
            })

    global FAISS_INDEX
    FAISS_INDEX = rebuild_faiss_index(IMAGE_DB, FAISS_DIM)


def query_text(query):
    global FAISS_INDEX

    text_tokens = clip.tokenize([query]).to(device)

    with torch.no_grad():
        text_features = model.encode_text(text_tokens)

    text_embedding = text_features.cpu().numpy()[0]
    text_embedding = normalize_vector(text_embedding).astype("float32").reshape(1, -1)

    if FAISS_INDEX is None or len(IMAGE_DB) == 0:
        return [], list(text_features.shape)

    top_k = min(3, len(IMAGE_DB))
    distances, indices = search_faiss_index(FAISS_INDEX, text_embedding, top_k)

    results = []
    for rank, idx in enumerate(indices[0]):
        img = IMAGE_DB[idx]

        distance = float(distances[0][rank])
        similarity_score = 1 / (1 + distance)

        label_boost = 0.05 if img["label"].lower() == query.lower() else 0.0
        final_score = similarity_score + label_boost


        results.append({
            "rank": rank + 1,
            "filename": img["filename"],
            "label": img["label"],
            "distance": round(distance, 4),
            "similarity_score": round(similarity_score, 4),
            "label_boost": round(label_boost, 4),
            "final_score": round(final_score, 4),
            "image_url": f"/curated/{img['filename']}" if img.get("source") == "curated" else f"/uploads/{img['filename']}"
        })


    results = sorted(results, key=lambda x: x["final_score"], reverse=True)

    for i, result in enumerate(results):
        result["rank"] = i + 1

    return results, list(text_features.shape)


def debug_images():
    return {
        "image_count": len(IMAGE_DB),
        "faiss_ready": FAISS_INDEX is not None,
        "images": [
            {
                "filename": img["filename"],
                "label": img["label"],
                "image_url": f"/curated/{img['filename']}" if img.get("source") == "curated" else f"/uploads/{img['filename']}"
            }
            for img in IMAGE_DB
        ]
    }


def get_vector_store_status():
    return get_faiss_status(FAISS_INDEX, FAISS_DIM)



def get_system_status():
    return {
        "image_count": len(IMAGE_DB),
        "device": device,
        **get_vector_store_status()
    }