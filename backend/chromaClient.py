import os
import uuid
import chromadb
from pathlib import Path
from dotenv import load_dotenv
import chromadb.utils.embedding_functions as embedding_functions

load_dotenv(Path(__file__).parent / ".env")

cohere_ef = embedding_functions.CohereEmbeddingFunction(
    api_key=os.getenv("CHROMA_COHERE_API_KEY"),
    model_name="embed-multilingual-light-v3.0"
)

chroma_client = chromadb.HttpClient(host="localhost", port=8000)


def _get_collection():
    return chroma_client.get_or_create_collection(
        name="cv_collection",
        embedding_function=cohere_ef
    )


def add_documents(texts: list[str]) -> None:
    """Add documents to the collection, skipping any that are already stored."""
    collection = _get_collection()
    existing = collection.get()["documents"] or []
    existing_set = set(existing)
    new_texts = [t for t in texts if t not in existing_set]
    if not new_texts:
        return
    ids = [str(uuid.uuid4()) for _ in new_texts]
    collection.upsert(ids=ids, documents=new_texts)


def store_cv_with_id(text: str, application_id: str) -> None:
    """Store a CV using the application_id as the document ID (upsert)."""
    collection = _get_collection()
    collection.upsert(ids=[application_id], documents=[text])


def rank_by_job(query_text: str, candidate_ids: list[str], n_results: int = 5) -> list[dict]:
    """Semantic search: return candidates from candidate_ids ranked by similarity to query_text."""
    collection = _get_collection()
    count = collection.count()
    if count == 0 or not candidate_ids:
        return []
    fetch_n = min(count, len(candidate_ids) + 30)
    results = collection.query(query_texts=[query_text], n_results=fetch_n)
    id_set = set(candidate_ids)
    ranked = []
    for doc_id, distance in zip(results["ids"][0], results["distances"][0]):
        if doc_id in id_set:
            ranked.append({"id": doc_id, "distance": distance})
        if len(ranked) >= n_results:
            break
    return ranked


def query(query_text: str, n_results: int = 1) -> list[dict]:
    """Query the collection and return a list of results with id, distance, and document."""
    collection = _get_collection()
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return [
        {"id": doc_id, "distance": distance, "document": document}
        for doc_id, distance, document in zip(
            results["ids"][0],
            results["distances"][0],
            results["documents"][0]
        )
    ]
