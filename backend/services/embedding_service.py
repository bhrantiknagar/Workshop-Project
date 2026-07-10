"""Cloud embedding service backed by Google's Gemini embedding API."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from flask import current_app, has_app_context
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from config import Config
from services.vector_store import add_embeddings

EMBEDDINGS_STORE: Dict[str, List[Dict[str, Any]]] = {}


class EmbeddingError(Exception):
    """Raised when an embedding operation fails."""


def _get_config_value(name: str, default: str) -> str:
    if has_app_context():
        return current_app.config.get(name, default)
    return getattr(Config, name, default)


def _get_embeddings_client() -> GoogleGenerativeAIEmbeddings:
    """Create a hosted embeddings client without loading a local model."""
    api_key = _get_config_value("GOOGLE_API_KEY", Config.GOOGLE_API_KEY) or os.getenv("GOOGLE_API_KEY", "")
    api_key = api_key.strip() if isinstance(api_key, str) else ""
    if not api_key:
        raise EmbeddingError("Google API key is missing. Add GOOGLE_API_KEY to your environment.")

    model = _get_config_value("GOOGLE_EMBEDDING_MODEL", Config.GOOGLE_EMBEDDING_MODEL)
    try:
        return GoogleGenerativeAIEmbeddings(model=model, google_api_key=api_key)
    except Exception as exc:
        raise EmbeddingError(f"Failed to configure cloud embeddings: {exc}") from exc


def embed_text(text: str) -> List[float]:
    """Generate a cloud embedding for one non-empty string."""
    if not isinstance(text, str) or not text.strip():
        raise EmbeddingError("Text to embed must be a non-empty string.")

    try:
        return [float(value) for value in _get_embeddings_client().embed_query(text)]
    except EmbeddingError:
        raise
    except Exception as exc:  # pragma: no cover - provider/network errors
        raise EmbeddingError(f"Failed to generate embedding for text: {exc}") from exc


def generate_embeddings_for_pdf(pdf_id: str, filename: str, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Embed PDF page chunks with the hosted provider and persist them in ChromaDB."""
    if not isinstance(pages, list):
        raise EmbeddingError("Invalid pages input; expected a list of page dicts.")

    chunks: List[Dict[str, Any]] = []
    for idx, page in enumerate(pages, start=1):
        text = (page.get("text") or "").strip()
        if not text:
            continue
        chunks.append(
            {
                "chunk_id": f"{pdf_id}_chunk_{idx:03d}",
                "pdf_id": pdf_id,
                "filename": filename,
                "page": page.get("page", idx),
                "text": text,
            }
        )

    if chunks:
        try:
            embeddings = _get_embeddings_client().embed_documents([chunk["text"] for chunk in chunks])
            if len(embeddings) != len(chunks):
                raise EmbeddingError("Cloud embedding provider returned an unexpected number of vectors.")
            for chunk, embedding in zip(chunks, embeddings):
                chunk["embedding"] = [float(value) for value in embedding]
            result = add_embeddings(chunks)
        except EmbeddingError:
            raise
        except Exception as exc:  # pragma: no cover - provider/database errors
            raise EmbeddingError(f"Failed to generate or persist embeddings for {filename}: {exc}") from exc
        stored, deleted = result.get("stored", 0), result.get("deleted", 0)
    else:
        stored = deleted = 0

    EMBEDDINGS_STORE[pdf_id] = chunks
    return {
        "filename": filename,
        "pdf_id": pdf_id,
        "chunks_created": len(chunks),
        "stored_embeddings": stored,
        "deleted_embeddings": deleted,
        "embedding_dim": len(chunks[0]["embedding"]) if chunks else 0,
        "status": "Generated" if chunks else "No chunks to embed",
    }


def generate_embeddings_for_all_pdfs(upload_folder: str) -> List[Dict[str, Any]]:
    """Extract and embed every PDF in the upload folder."""
    from services.pdf_service import extract_text

    summaries = []
    for pdf_path in sorted(Path(upload_folder).glob("*.pdf")):
        try:
            summaries.append(generate_embeddings_for_pdf(pdf_path.stem, pdf_path.name, extract_text(pdf_path)))
        except EmbeddingError:
            raise
        except Exception as exc:  # pragma: no cover - file read/runtime errors
            raise EmbeddingError(f"Failed processing {pdf_path.name}: {exc}") from exc
    return summaries


def list_embeddings(pdf_id: Optional[str] = None):
    """Return embeddings generated during the current process."""
    return EMBEDDINGS_STORE.get(pdf_id, []) if pdf_id else EMBEDDINGS_STORE


def clear_store() -> None:
    """Clear in-memory embedding metadata (useful for tests)."""
    EMBEDDINGS_STORE.clear()
