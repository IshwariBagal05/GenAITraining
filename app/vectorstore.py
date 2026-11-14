from pathlib import Path

import chromadb

from app.chunking import load_chunks
from app.embed import get_embedding_function

DB_DIR = Path(__file__).resolve().parent.parent / "chroma_db"
COLLECTION = "insureclear_chunks"


def _client():
    return chromadb.PersistentClient(path=str(DB_DIR))


def get_collection():
    return _client().get_or_create_collection(
        name=COLLECTION, embedding_function=get_embedding_function()
    )


def index_all():
    """(Re)build the collection from all chunks. Returns the number indexed."""
    chunks = load_chunks()
    if not chunks:
        raise RuntimeError("No chunks found. Check data/raw/ and app/ingest.py.")

    client = _client()
    try:
        client.delete_collection(COLLECTION)      # start clean so re-runs never duplicate
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION, embedding_function=get_embedding_function()
    )
    collection.add(
        ids=[c["id"] for c in chunks],
        documents=[c["text"] for c in chunks],
        metadatas=[{"source": c["source"], "page": c["page"], "title": c["title"],
                    "slug": c["slug"], "chunk_index": c["chunk_index"]}
                   for c in chunks],
    )
    return len(chunks)


def query(question, n_results=3):
    """Return the closest chunks. 'distance' is lower for closer matches."""
    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError("The index is empty. Run: python -m app.vectorstore")

    res = collection.query(query_texts=[question], n_results=n_results)
    hits = []
    for i, chunk_id in enumerate(res["ids"][0]):
        meta = res["metadatas"][0][i]
        hits.append({
            "id": chunk_id,
            "title": meta["title"],
            "source": meta["source"],
            "page": meta["page"],
            "text": res["documents"][0][i],
            "distance": round(float(res["distances"][0][i]), 4),
        })
    return hits


if __name__ == "__main__":
    print(f"Indexed {index_all()} chunks into {DB_DIR}")