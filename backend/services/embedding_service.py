"""Embedding service using SentenceTransformers.

This module generates embeddings for text chunks and stores them
in-memory as structured records. It intentionally does not persist
to any database — that will be implemented in a later phase.
"""
from pathlib import Path
from typing import List, Dict, Any

from services.vector_store import add_embeddings

_MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDINGS_STORE: Dict[str, List[Dict[str, Any]]] = {}
_MODEL = None


class EmbeddingError(Exception):
    """Raised when an embedding operation fails."""


def _load_model():
    """Lazily load the sentence-transformers model.

    Raises EmbeddingError on failure.
    """
    global _MODEL

    if _MODEL is not None:
        return _MODEL

    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except ModuleNotFoundError as exc:  # pragma: no cover - environment dependent
        raise EmbeddingError("sentence-transformers is not installed.") from exc

    try:
        _MODEL = SentenceTransformer(_MODEL_NAME)
    except Exception as exc:  # pragma: no cover - model download/runtime issues
        raise EmbeddingError(f"Failed to load embedding model '{_MODEL_NAME}': {exc}") from exc

    return _MODEL


def _to_list(vector) -> List[float]:
    """Convert numpy array or tensor to plain Python list of floats."""
    try:
        return vector.tolist()
    except Exception:
        return [float(v) for v in vector]


def generate_embeddings_for_pdf(pdf_id: str, filename: str, pages: List[Dict[str, Any]]):
    """Generate embeddings for each text chunk (page) in a PDF.

    Args:
        pdf_id: unique identifier for the PDF (e.g. 'pdf_001').
        filename: original filename for display.
        pages: list of page dicts with keys `page` (int) and `text` (str).

    Returns:
        summary dict with filename, pdf_id, chunks_created, embedding_dim, status

    Raises:
        EmbeddingError for model/load failures or invalid input.
    """
    if not isinstance(pages, list):
        raise EmbeddingError("Invalid pages input; expected a list of page dicts.")

    model = _load_model()

    chunks = []
    for idx, page in enumerate(pages, start=1):
        text = (page.get("text") or "").strip()
        if not text:
            # skip empty page chunks
            continue

        chunk_id = f"{pdf_id}_chunk_{idx:03d}"
        try:
            vector = model.encode(text)
            embedding = _to_list(vector)
        except Exception as exc:  # pragma: no cover - runtime encoding errors
            raise EmbeddingError(f"Failed to generate embedding for chunk {chunk_id}: {exc}") from exc

        chunks.append(
            {
                "chunk_id": chunk_id,
                "pdf_id": pdf_id,
                "filename": filename,
                "page": page.get("page", idx),
                "text": text,
                "embedding": embedding,
            }
        )

    EMBEDDINGS_STORE[pdf_id] = chunks

    if chunks:
        try:
            result = add_embeddings(chunks)
        except Exception as exc:
            raise EmbeddingError(f"Failed to persist embeddings for PDF {pdf_id}: {exc}") from exc
        stored = result.get("stored", 0)
        deleted = result.get("deleted", 0)
    else:
        stored = 0
        deleted = 0

    embedding_dim = len(chunks[0]["embedding"]) if chunks else 0

    return {
        "filename": filename,
        "pdf_id": pdf_id,
        "chunks_created": len(chunks),
        "stored_embeddings": stored,
        "deleted_embeddings": deleted,
        "embedding_dim": embedding_dim,
        "status": "Generated" if chunks else "No chunks to embed",
    }


def generate_embeddings_for_all_pdfs(upload_folder: str):
    """Scan the upload folder, extract text, and generate embeddings for each PDF.

    Returns a list of summary dicts for each PDF processed.
    """
    from services.pdf_service import extract_text

    upload_path = Path(upload_folder)
    summaries = []

    for pdf_path in sorted(upload_path.glob("*.pdf")):
        pdf_id = pdf_path.stem
        filename = pdf_path.name
        try:
            pages = extract_text(pdf_path)
            summary = generate_embeddings_for_pdf(pdf_id, filename, pages)
        except EmbeddingError:
            raise
        except Exception as exc:  # pragma: no cover - file read/runtime issues
            raise EmbeddingError(f"Failed processing {filename}: {exc}") from exc

        summaries.append(summary)

    return summaries


def list_embeddings(pdf_id: str = None):
    """Return stored embeddings. If `pdf_id` is provided, return only that PDF's chunks."""
    if pdf_id:
        return EMBEDDINGS_STORE.get(pdf_id, [])
    return EMBEDDINGS_STORE


def clear_store():
    """Clear in-memory embeddings (useful for tests)."""
    EMBEDDINGS_STORE.clear()

