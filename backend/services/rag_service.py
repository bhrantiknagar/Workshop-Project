"""Retrieval-Augmented Generation (RAG) service.

This module implements single-question RAG using the existing
`search_similar_chunks` function for retrieval and a swappable LLM provider
for the final generation step.

Responsibilities:
- Receive a user question
- Retrieve the top-k relevant chunks from ChromaDB
- Build a prompt containing a system instruction + retrieved context
- Send the retrieved context to the selected LLM and return the answer/sources

The RAG logic is intentionally thin and delegates embedding/search to
`services.vector_store` and LLM calls to provider adapter modules.
"""
from typing import Dict, List, Optional, Set, Tuple

from services.vector_store import search_similar_chunks, VectorStoreError
from services.llm_service import LLMServiceError
from services import groq_service, ollama_service


PROVIDERS = {
    "groq": {
        "label": "Groq Cloud",
        "generate": groq_service.generate_answer,
    },
    "ollama": {
        "label": "Ollama Local",
        "generate": ollama_service.generate_answer,
    },
}


def _format_context(chunks: List[Dict]) -> str:
    """Format retrieved chunks into a context string for the prompt.

    Each chunk is annotated with filename and page to allow the model to
    reference sources in its answer.
    """
    parts: List[str] = []
    for i, c in enumerate(chunks, start=1):
        filename = c.get("filename") or "unknown.pdf"
        page = c.get("page") or "?"
        text = (c.get("text") or "").strip()
        parts.append(f"[Source {i}] {filename} (page {page}):\n{text}\n")
    return "\n".join(parts)


def _truncate_chunks_for_prompt(chunks: List[Dict], max_chars: int = 8000) -> List[Dict]:
    """Return a prefix of `chunks` whose formatted context is within `max_chars`.

    This is a simple character-count based truncation to avoid sending
    excessively large prompts to the Ollama service which can cause timeouts.
    We preserve chunk order (most relevant first) and include as many chunks
    as fit under the limit.
    """
    selected: List[Dict] = []
    total = 0
    for c in chunks:
        filename = c.get("filename") or "unknown.pdf"
        page = c.get("page") or "?"
        text = (c.get("text") or "").strip()
        part = f"[Source] {filename} (page {page}):\n{text}\n\n"
        if total + len(part) > max_chars:
            break
        selected.append(c)
        total += len(part)

    return selected


def _collect_sources(chunks: List[Dict]) -> List[Dict[str, int]]:
    """Return a deduplicated list of source filename/page dicts.

    Output format: [{"filename": <str>, "page": <int>}, ...]
    """
    seen: Set[Tuple[str, int]] = set()
    out: List[Dict[str, int]] = []
    for c in chunks:
        fn = c.get("filename") or "unknown.pdf"
        pg = c.get("page") or None
        key = (fn, pg)
        if key not in seen:
            seen.add(key)
            out.append({"filename": fn, "page": pg})
    return out


def _resolve_provider(provider: Optional[str]) -> Tuple[str, Dict]:
    """Return a supported provider key/config, defaulting to Groq Cloud."""
    provider_key = (provider or "groq").strip().lower()
    if provider_key not in PROVIDERS:
        provider_key = "groq"
    return provider_key, PROVIDERS[provider_key]


def answer_with_rag(
    question: str,
    top_k: int = 12,
    model: Optional[str] = None,
    timeout: int = 60,
    pdf_ids: Optional[List[str]] = None,
    provider: Optional[str] = None,
) -> Dict:
    """Answer a single question using retrieved PDF context and an LLM provider.

    Returns a dict with keys:
    - `answer`: the LLM-generated text
    - `sources`: list of {filename, page} dicts used to produce the answer
    - `provider`: provider key used for the final generation step
    - `provider_label`: user-facing provider label

    Raises:
        VectorStoreError: if retrieval fails or question invalid
        LLMServiceError: if the selected LLM cannot produce an answer
    """
    if not isinstance(question, str) or not question.strip():
        raise VectorStoreError("Question must be a non-empty string.")

    provider_key, provider_config = _resolve_provider(provider)

    # Retrieve relevant chunks, optionally restricting to provided pdf_ids
    chunks = search_similar_chunks(question, top_k=top_k, pdf_ids=pdf_ids)

    if not chunks:
        # No retrieved context; return a clear not-found message without calling LLM
        return {
            "answer": "I couldn't find that information in the uploaded PDF.",
            "sources": [],
            "provider": provider_key,
            "provider_label": provider_config["label"],
        }

    # Optionally truncate retrieved chunks to keep prompt size reasonable.
    truncated_chunks = _truncate_chunks_for_prompt(chunks, max_chars=4000)

    context = _format_context(truncated_chunks)

    # Retrieval stays identical; only this final generation provider changes.
    try:
        answer_text = provider_config["generate"](
            context,
            question.strip(),
            model=model,
            timeout=timeout,
        )
    except LLMServiceError:
        # Re-raise LLM errors to be handled by the route layer.
        raise

    sources = _collect_sources(chunks)

    return {
        "answer": answer_text,
        "sources": sources,
        "provider": provider_key,
        "provider_label": provider_config["label"],
    }
