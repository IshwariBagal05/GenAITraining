import numpy as np
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

_ef = None


def get_embedding_function():
    """One shared embedding model (local MiniLM). Downloads once on first use."""
    global _ef
    if _ef is None:
        _ef = DefaultEmbeddingFunction()
    return _ef


def embed_texts(texts):
    """Turn a list of strings into a 2-D numpy array of vectors."""
    vectors = get_embedding_function()(list(texts))
    return np.array(vectors, dtype="float32")


def search_matrix(query, chunks, matrix, top_k=3):
    """Rank chunks by cosine similarity to the query (1.0 = same meaning)."""
    q = embed_texts([query])[0]
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
    scores = (matrix @ q) / np.where(norms == 0, 1, norms)
    order = scores.argsort()[::-1][:top_k]
    return [{**chunks[i], "score": round(float(scores[i]), 4)} for i in order]