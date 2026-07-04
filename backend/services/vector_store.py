"""ChromaDB persistence helpers for SmartPDF AI."""
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings

from config import Config

COLLECTION_NAME = "smartpdf_documents"


class VectorStoreError(Exception):
    """Raised when ChromaDB operations fail."""


def _get_client() -> chromadb.Client:
    """Create or return a persistent ChromaDB client."""
    db_path = Path(Config.CHROMA_DB_PATH)
    db_path.mkdir(parents=True, exist_ok=True)
    settings = Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=str(db_path),
    )
    return chromadb.Client(settings)


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


def add_embeddings(chunks: List[Dict[str, Any]]) -> int:
    """Add embeddings to the smartpdf_documents collection.

    Duplicate chunk IDs are removed before insertion.
    Returns the number of embeddings stored.
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

    delete_pdf_embeddings(pdf_id)

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
    client.persist()
    return len(ids)


def delete_pdf_embeddings(pdf_id: str) -> int:
    """Remove all embeddings for a given PDF from the collection."""
    if not isinstance(pdf_id, str) or not pdf_id.strip():
        raise VectorStoreError("pdf_id must be a non-empty string.")

    collection = create_collection()
    existing = collection.get(where={"pdf_id": pdf_id}, include=["ids"])
    ids = _flatten_list(existing.get("ids", []))
    if not ids:
        return 0

    collection.delete(ids=ids)
    _get_client().persist()
    return len(ids)


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
