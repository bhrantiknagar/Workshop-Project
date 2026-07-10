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

    try:
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings,
        )
    except Exception as exc:
        # Existing databases may contain vectors from the retired local model.
        # Chroma collections require one vector dimension, so recreate only when
        # that legacy collection conflicts with the hosted embedding dimension.
        if "dimension" not in str(exc).lower():
            raise VectorStoreError(f"Failed to add embeddings: {exc}") from exc
        try:
            client.delete_collection(collection.name)
            collection = create_collection()
            collection.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=embeddings)
            deleted = 0
        except Exception as reset_exc:
            raise VectorStoreError(f"Failed to recreate incompatible embedding collection: {reset_exc}") from reset_exc
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


def _convert_distance_to_score(distance: float) -> float:
    """Convert a ChromaDB distance to a percentage similarity score (0-100).

    ChromaDB may return distances where 0.0 means identical (cosine distance).
    We attempt a robust conversion: when distance is within [0,1], score = (1 - distance)*100.
    Otherwise, if distance looks like a similarity already, clamp to [0,100].
    """
    # Robust conversion that handles different ChromaDB return conventions:
    # - Some versions return a distance in [0, 2] (cosine distance where 0==identical, 2==opposite).
    # - Others return a distance in [0, 1] where 0==identical (e.g., some L2-normalized distances).
    # - Some clients may return a similarity in [0, 1] (higher == more similar).
    #
    # Heuristic used below:
    # 1. If value in [0, 2]:
    #    - If >1.0 we assume it is the cosine-distance in [0,2] and convert with (1 - d/2).
    #    - If in [0,1]: we decide between "distance" vs "similarity" by thresholding at 0.5.
    #      - If value >= 0.5 -> likely a similarity score (higher == more similar) so use val*100.
    #      - Else treat as a distance (lower == more similar) so use (1 - val)*100.
    # 2. If value outside expected ranges, clamp to [0,100].
    try:
        val = float(distance)
        # Cosine distance in [0,2]
        if 0.0 <= val <= 2.0:
            if val > 1.0:
                # Map [0,2] -> similarity percent: 0 -> 100%, 2 -> 0%
                return round(max(0.0, (1.0 - (val / 2.0))) * 100.0, 2)

            # val is in [0,1]. Could be distance (0==identical) or similarity (1==identical).
            # Use a simple heuristic: values >= 0.5 are more likely to be similarity scores.
            if val >= 0.5:
                return round(val * 100.0, 2)
            return round(max(0.0, (1.0 - val)) * 100.0, 2)

        # If it's already on a 0-1 similarity scale
        if 0.0 <= val <= 1.0:
            return round(val * 100.0, 2)

        # Otherwise clamp to 0-100
        return round(max(0.0, min(val, 100.0)), 2)
    except Exception:
        return 0.0


def search_similar_chunks(question: str, top_k: int = 5, pdf_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """Search the `smartpdf_documents` collection for chunks similar to `question`.

    Workflow:
    - Generate an embedding for `question` using the same embedding model.
    - Query ChromaDB for the top_k nearest results.

    Returns a list of results sorted by descending similarity score. Each result
    contains: `filename`, `page`, `text`, `similarity`.

    Raises:
        VectorStoreError: on invalid input or ChromaDB errors.
    """
    if not isinstance(question, str) or not question.strip():
        raise VectorStoreError("Question must be a non-empty string.")

    try:
        # Lazily import embedding helper to avoid circular imports at module import time
        from services.embedding_service import embed_text
    except Exception as exc:
        raise VectorStoreError(f"Embedding service unavailable: {exc}") from exc

    try:
        query_embedding = embed_text(question)
    except Exception as exc:
        raise VectorStoreError(f"Failed to create query embedding: {exc}") from exc

    client = _get_client()
    collection = create_collection()

    # Handle empty collection
    try:
        if collection.count() == 0:
            return []
    except Exception:
        # If collection.count() not available or fails, continue and let query fail if needed
        pass

    # Build optional `where` filter to restrict search to provided pdf_ids
    where = None
    if pdf_ids:
        # Normalize to list of strings
        pdf_ids = [str(x) for x in pdf_ids if x]
        if pdf_ids:
            # ChromaDB supports `$in` style filters in newer versions; use a
            # conservative approach that works for single or multiple ids.
            where = {"pdf_id": pdf_ids[0]} if len(pdf_ids) == 1 else {"pdf_id": {"$in": pdf_ids}}

    # Use query API if available
    query_fn = getattr(collection, "query", None)
    if not callable(query_fn):
        raise VectorStoreError("ChromaDB collection.query() not available in this client version.")

    try:
        # Some ChromaDB versions reject unknown include items (e.g. 'ids'),
        # so only request the widely-supported fields here.
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k,
            "include": ["metadatas", "documents", "distances"],
        }
        if where is not None:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)
    except Exception as exc:
        # If filtering by multiple pdf_ids using a single `where` clause
        # fails (older chromadb versions may not support `$in`), fall back
        # to querying each pdf_id separately and merging the results.
        if pdf_ids and len(pdf_ids) > 1:
            try:
                merged = []
                for pid in pdf_ids:
                    try:
                        small_kwargs = {
                            "query_embeddings": [query_embedding],
                            "n_results": top_k,
                            "include": ["metadatas", "documents", "distances"],
                            "where": {"pdf_id": pid},
                        }
                        part = collection.query(**small_kwargs)
                    except Exception:
                        # Skip PDFs that cannot be queried individually
                        continue

                    docs = _flatten_list(part.get("documents", []))
                    metas = _flatten_list(part.get("metadatas", []))
                    dists = _flatten_list(part.get("distances", []))

                    for d_idx, dist in enumerate(dists):
                        merged.append((dist, docs[d_idx] if d_idx < len(docs) else "", metas[d_idx] if d_idx < len(metas) else {}))

                # Sort merged results by ascending distance and take top_k
                merged.sort(key=lambda t: t[0])
                top = merged[:top_k]

                results = {
                    "documents": [t[1] for t in top],
                    "metadatas": [t[2] for t in top],
                    "distances": [t[0] for t in top],
                }
            except Exception as exc2:
                raise VectorStoreError(f"ChromaDB query failed: {exc2}") from exc2
        else:
            raise VectorStoreError(f"ChromaDB query failed: {exc}") from exc

    # Results are typically nested lists (one list per query). Flatten to single lists.
    ids = _flatten_list(results.get("ids", []))
    docs = _flatten_list(results.get("documents", []))
    metadatas = _flatten_list(results.get("metadatas", []))
    distances = _flatten_list(results.get("distances", []))

    # If a pdf_ids filter was provided, ensure results only include entries
    # whose metadata `pdf_id` is in the allowed list. Some ChromaDB client
    # versions ignore the `where` clause, so we defensively filter here.
    if pdf_ids:
        allowed = set(str(x) for x in pdf_ids if x)
        filtered_docs = []
        filtered_metas = []
        filtered_dists = []
        filtered_ids = []
        for i, meta in enumerate(metadatas):
            pid = None
            if isinstance(meta, dict):
                pid = meta.get("pdf_id")
            if pid and str(pid) in allowed:
                filtered_docs.append(docs[i] if i < len(docs) else "")
                filtered_metas.append(meta)
                filtered_dists.append(distances[i] if i < len(distances) else None)
                filtered_ids.append(ids[i] if i < len(ids) else None)

        docs, metadatas, distances, ids = filtered_docs, filtered_metas, filtered_dists, filtered_ids

    output: List[Dict[str, Any]] = []
    for idx, dist in enumerate(distances):
        try:
            doc = docs[idx] if idx < len(docs) else ""
            meta = metadatas[idx] if idx < len(metadatas) else {}
            score = _convert_distance_to_score(dist)
            # Determine whether the returned value is being shown as a similarity
            # or a raw distance. If the conversion produced a percent > 0 then
            # we present it as a similarity; otherwise show the raw distance.
            display_type = "similarity" if score > 0 else "distance"
            output.append(
                {
                    "filename": meta.get("filename") if isinstance(meta, dict) else None,
                    "page": meta.get("page") if isinstance(meta, dict) else None,
                    "text": doc,
                    "raw_distance": dist,
                    "similarity": score,
                    "display_type": display_type,
                }
            )
        except Exception:
            continue

    # Sort by descending similarity
    output.sort(key=lambda r: r.get("similarity", 0.0), reverse=True)
    return output
