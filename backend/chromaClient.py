import os
import uuid
import chromadb
from dotenv import load_dotenv
import chromadb.utils.embedding_functions as embedding_functions

load_dotenv()

cohere_ef = embedding_functions.CohereEmbeddingFunction(
    api_key=os.getenv("COHERE_API_KEY"),
    model_name="embed-multilingual-light-v3.0"
)

chroma_client = chromadb.HttpClient(host="localhost", port=8000)

collection = chroma_client.get_or_create_collection(
    name="cv_collection",
    embedding_function=cohere_ef
)


def add_documents(texts: list[str]) -> None:
    """Add a list of text documents to the collection."""
    ids = [str(uuid.uuid4()) for _ in texts]
    collection.upsert(ids=ids, documents=texts)


def query(query_text: str, n_results: int = 1) -> list[dict]:
    """Query the collection and return a list of results with id, distance, and document."""
    results = collection.query(query_texts=[query_text], n_results=n_results)
    return [
        {"id": doc_id, "distance": distance, "document": document}
        for doc_id, distance, document in zip(
            results["ids"][0],
            results["distances"][0],
            results["documents"][0]
        )
    ]
