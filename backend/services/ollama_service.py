"""Ollama provider adapter for SmartPDF AI."""

from typing import Optional

from services.llm_service import generate_llm_response


SYSTEM_INSTRUCTION = (
    "You are SmartPDF AI. Answer ONLY using the provided PDF context. "
    "Format answers for readability: use short paragraphs, numbered lists, "
    "or bullet points when listing details. Put each list item on its own line. "
    "If the answer cannot be found in the provided context, reply:\n"
    "I couldn't find that information in the uploaded PDF."
)


def build_rag_prompt(context: str, question: str) -> str:
    """Build the shared RAG prompt used by every LLM provider."""
    return f"{SYSTEM_INSTRUCTION}\n\nContext:\n{context}\nQuestion:\n{question.strip()}\n"


def generate_answer(
    context: str,
    question: str,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """Generate an answer with the existing local Ollama implementation."""
    prompt = build_rag_prompt(context, question)
    return generate_llm_response(prompt, model=model, timeout=timeout)
