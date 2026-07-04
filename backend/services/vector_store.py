"""ChromaDB persistence helpers for SmartPDF AI."""
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb

from config import Config

COLLECTION_NAME = "smartpdf_documents"


class VectorStoreError(Exception):
    """Raised when ChromaDB operations fail."""


def _get_client():
    """Create or return a persistent ChromaDB client."""
    db_path = Path(Config.CHROMA_DB_PATH)
    db_path.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(db_path))


def _maybe_persist(client) -> bool:
    """Attempt to persist the ChromaDB client if the method exists.

    Returns True if a persist operation was attempted, False otherwise.
    """
    try:
        persist_fn = getattr(client, "persist", None)
        if callable(persist_fn):
            persist_fn()
            return True
    except Exception:
        # If persistence fails for any reason, don't crash the app here.
        return False

    return False


def create_collection(name: Optional[str] = None):
    """Create or return the ChromaDB collection for SmartPDF.

    Args:
        name: The collection name to use. Defaults to smartpdf_documents.
    """
    client = _get_client()
    return client.get_or_create_collection(
        name=name or COLLECTION_NAME,
        metadata={"source": "smartpdf_ai"},
    )


def _validate_chunk(chunk: Dict[str, Any]):
    """Validate a chunk dictionary before storing it."""
    missing = [key for key in ("chunk_id", "pdf_id", "filename", "page", "text", "embedding") if key not in chunk]
    if missing:
        raise VectorStoreError(f"Missing required chunk fields: {', '.join(missing)}")

    if not isinstance(chunk["embedding"], list) or not chunk["embedding"]:
        raise VectorStoreError("Chunk embedding must be a non-empty list.")

    if not isinstance(chunk["chunk_id"], str) or not chunk["chunk_id"].strip():
        raise VectorStoreError("Chunk must have a valid string chunk_id.")

    if not isinstance(chunk["pdf_id"], str) or not chunk["pdf_id"].strip():
        raise VectorStoreError("Chunk must have a valid string pdf_id.")

    if not isinstance(chunk["filename"], str) or not chunk["filename"].strip():
        raise VectorStoreError("Chunk must have a valid filename.")

    if not isinstance(chunk["page"], int) or chunk["page"] <= 0:
        raise VectorStoreError("Chunk page must be a positive integer.")


def _flatten_list(value: Any) -> List[Any]:
    """Flatten nested list output returned by ChromaDB get operations."""
    if value is None:
        return []
    if isinstance(value, list) and value and isinstance(value[0], list):
        return [item for sublist in value for item in sublist]
    if isinstance(value, list):
        return value
    return [value]


def add_embeddings(chunks: List[Dict[str, Any]]) -> Dict[str, int]:
    """Add embeddings to the smartpdf_documents collection.

    Duplicate chunk IDs are removed before insertion.
    Returns the number of embeddings deleted and stored.
    """
    if not isinstance(chunks, list) or not chunks:
        raise VectorStoreError("No chunk embeddings provided.")

    client = _get_client()
    collection = create_collection()
    pdf_id = chunks[0].get("pdf_id")
    if any(chunk.get("pdf_id") != pdf_id for chunk in chunks):
        raise VectorStoreError("All chunks must share the same pdf_id.")

    for chunk in chunks:
        _validate_chunk(chunk)

    deleted = delete_pdf_embeddings(pdf_id)

    ids = [chunk["chunk_id"] for chunk in chunks]
    documents = [chunk["text"] for chunk in chunks]
    embeddings = [chunk["embedding"] for chunk in chunks]
    metadatas = [
        {
            "pdf_id": chunk["pdf_id"],
            "filename": chunk["filename"],
            "page": chunk["page"],
        }
        for chunk in chunks
    ]

    collection.add(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
        embeddings=embeddings,
    )
    # Some chromadb client versions expose a `persist()` method on the
    # client; others persist automatically or expose different APIs.
    # Call persist if available, but don't raise if it's not present.
    _maybe_persist(client)
    return {"deleted": deleted, "stored": len(ids)}


def delete_pdf_embeddings(pdf_id: str) -> int:
    """Remove all embeddings for a given PDF from the collection."""
    if not isinstance(pdf_id, str) or not pdf_id.strip():
        raise VectorStoreError("pdf_id must be a non-empty string.")

    collection = create_collection()
    delete_result = collection.delete(where={"pdf_id": pdf_id})
    # Attempt to persist client state if supported by the installed chromadb.
    try:
        _maybe_persist(_get_client())
    except Exception:
        pass

    # ChromaDB DeleteResult may include a count of removed ids.
    return len(delete_result.ids) if hasattr(delete_result, "ids") else 0


def get_collection_info() -> Dict[str, Any]:
    """Return information about the smartpdf_documents collection."""
    collection = create_collection()
    total_embeddings = collection.count()
    metadata = _flatten_list(collection.get(include=["metadatas"]).get("metadatas", []))
    unique_pdf_ids = {item.get("pdf_id") for item in metadata if isinstance(item, dict) and item.get("pdf_id")}

    return {
        "collection_name": collection.name,
        "documents": len(unique_pdf_ids),
        "embeddings": total_embeddings,
        "status": "Connected",
    }
