"""Retrieval-Augmented Generation (RAG) service.

This module implements single-question RAG using the existing
`search_similar_chunks` function for retrieval and `llm_service` for
generation via Ollama.

Responsibilities:
- Receive a user question
- Retrieve the top-k relevant chunks from ChromaDB
- Build a prompt containing a system instruction + retrieved context
- Send the prompt to Ollama and return the answer and sources

The RAG logic is intentionally thin and delegates embedding/search to
`services.vector_store` and LLM calls to `services.llm_service`.
"""
from typing import Dict, List, Optional, Set, Tuple

from services.vector_store import search_similar_chunks, VectorStoreError
from services.llm_service import LLMServiceError, generate_llm_response


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


def answer_with_rag(question: str, top_k: int = 12, model: Optional[str] = None, timeout: int = 60, pdf_ids: Optional[List[str]] = None) -> Dict:
    """Answer a single question using retrieved PDF context and Ollama.

    Returns a dict with keys:
    - `answer`: the LLM-generated text
    - `sources`: list of {filename, page} dicts used to produce the answer

    Raises:
        VectorStoreError: if retrieval fails or question invalid
        LLMServiceError: if Ollama cannot produce an answer
    """
    if not isinstance(question, str) or not question.strip():
        raise VectorStoreError("Question must be a non-empty string.")

    # Retrieve relevant chunks, optionally restricting to provided pdf_ids
    chunks = search_similar_chunks(question, top_k=top_k, pdf_ids=pdf_ids)

    if not chunks:
        # No retrieved context; return a clear not-found message without calling LLM
        return {
            "answer": "I couldn't find that information in the uploaded PDF.",
            "sources": [],
        }

    # Optionally truncate retrieved chunks to keep prompt size reasonable.
    truncated_chunks = _truncate_chunks_for_prompt(chunks, max_chars=4000)

    # Build prompt
    system_instruct = (
        "You are SmartPDF AI. Answer ONLY using the provided PDF context. "
        "If the answer cannot be found in the provided context, reply:\n"
        "I couldn't find that information in the uploaded PDF."
    )

    context = _format_context(truncated_chunks)

    prompt = (
        f"{system_instruct}\n\nContext:\n{context}\nQuestion:\n{question.strip()}\n"
    )

    # Ask Ollama
    try:
        answer_text = generate_llm_response(prompt, model=model, timeout=timeout)
    except LLMServiceError:
        # Re-raise LLM errors to be handled by the route layer.
        raise

    sources = _collect_sources(chunks)

    return {"answer": answer_text, "sources": sources}
