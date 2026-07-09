"""PDF comparison service built on the existing RAG retrieval flow."""

from typing import Dict, List, Optional, Set, Tuple

from services.llm_service import LLMServiceError
from services.rag_service import PROVIDERS
from services.vector_store import VectorStoreError, search_similar_chunks


def _format_pdf_context(label: str, chunks: List[Dict]) -> str:
    """Format one PDF's retrieved chunks with document labels and page numbers."""
    if not chunks:
        return f"{label}: No relevant context was found for this document."

    parts = []
    for index, chunk in enumerate(chunks, start=1):
        filename = chunk.get("filename") or label
        page = chunk.get("page") or "?"
        text = (chunk.get("text") or "").strip()
        parts.append(f"[{label} Source {index}] {filename} (page {page}):\n{text}")
    return "\n\n".join(parts)


def _collect_source_pages(chunks: List[Dict]) -> Dict[str, List[int]]:
    """Return source pages grouped by filename."""
    pages_by_file: Dict[str, Set[int]] = {}
    for chunk in chunks:
        filename = chunk.get("filename") or "unknown.pdf"
        page = chunk.get("page")
        pages_by_file.setdefault(filename, set())
        if isinstance(page, int):
            pages_by_file[filename].add(page)

    return {filename: sorted(pages) for filename, pages in pages_by_file.items()}


def _format_sources_section(pdf_a_chunks: List[Dict], pdf_b_chunks: List[Dict]) -> str:
    """Build a deterministic sources section from retrieved chunks."""
    grouped_sources = _collect_source_pages(pdf_a_chunks + pdf_b_chunks)
    if not grouped_sources:
        return "Sources\nNo relevant pages found."

    lines = ["Sources"]
    for filename, pages in grouped_sources.items():
        lines.append(filename)
        if pages:
            lines.extend(f"Page {page}" for page in pages)
        else:
            lines.append("No relevant pages found.")
    return "\n".join(lines)


def _resolve_provider(provider: Optional[str]) -> Tuple[str, Dict]:
    provider_key = (provider or "groq").strip().lower()
    if provider_key not in PROVIDERS:
        provider_key = "groq"
    return provider_key, PROVIDERS[provider_key]


def compare_pdfs(
    prompt: str,
    pdf_ids: List[str],
    provider: Optional[str] = None,
    top_k: int = 8,
    timeout: int = 60,
) -> Dict:
    """Compare two PDFs by searching each document independently."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise VectorStoreError("Comparison prompt must be a non-empty string.")

    pdf_ids = [str(pdf_id) for pdf_id in (pdf_ids or []) if pdf_id]
    if len(pdf_ids) != 2:
        raise VectorStoreError("Upload exactly two PDFs before comparing.")

    provider_key, provider_config = _resolve_provider(provider)

    pdf_a_chunks = search_similar_chunks(prompt, top_k=top_k, pdf_ids=[pdf_ids[0]])
    pdf_b_chunks = search_similar_chunks(prompt, top_k=top_k, pdf_ids=[pdf_ids[1]])

    if not pdf_a_chunks and not pdf_b_chunks:
        return {
            "answer": (
                "Overview\n"
                "No relevant context was found in either uploaded PDF for this comparison.\n\n"
                "Sources\nNo relevant pages found."
            ),
            "provider": provider_key,
            "provider_label": provider_config["label"],
            "sources": [],
        }

    context = (
        "Compare the following two PDF contexts only. Never invent details.\n\n"
        "PDF 1 Context:\n"
        f"{_format_pdf_context('PDF 1', pdf_a_chunks)}\n\n"
        "PDF 2 Context:\n"
        f"{_format_pdf_context('PDF 2', pdf_b_chunks)}"
    )
    comparison_question = (
        f"What would you like to compare?\n{prompt.strip()}\n\n"
        "Return the answer using exactly these sections:\n"
        "Overview\n"
        "Comparison Table\n"
        "Key Differences\n"
        "Key Similarities\n"
        "Conclusion\n"
        "Sources\n\n"
        "In the comparison table, include a column for PDF 1 and a column for PDF 2. "
        "Clearly mention when one PDF does not contain relevant information. "
        "For every important statement, identify whether it came from PDF 1 or PDF 2. "
        "Use only the provided contexts."
    )

    try:
        answer_text = provider_config["generate"](
            context,
            comparison_question,
            model=None,
            timeout=timeout,
        )
    except LLMServiceError:
        raise

    sources_section = _format_sources_section(pdf_a_chunks, pdf_b_chunks)
    if "sources" not in answer_text.lower():
        answer_text = f"{answer_text.strip()}\n\n{sources_section}"

    return {
        "answer": answer_text.strip(),
        "provider": provider_key,
        "provider_label": provider_config["label"],
        "sources": _collect_source_pages(pdf_a_chunks + pdf_b_chunks),
    }
