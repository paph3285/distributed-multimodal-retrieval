import numpy as np
import faiss


def rebuild_faiss_index(image_db, faiss_dim):
    faiss_index = faiss.IndexFlatL2(faiss_dim)

    if len(image_db) == 0:
        return faiss_index

    embedding_matrix = np.array(
        [img["embedding"] for img in image_db],
        dtype="float32"
    )

    faiss_index.add(embedding_matrix)
    return faiss_index


def search_faiss_index(faiss_index, query_embedding, top_k):
    return faiss_index.search(query_embedding, top_k)


def get_faiss_status(faiss_index, faiss_dim):
    return {
        "faiss_ready": faiss_index is not None,
        "vector_count": faiss_index.ntotal if faiss_index is not None else 0,
        "faiss_dim": faiss_dim
    }