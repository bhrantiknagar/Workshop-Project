"""Groq provider adapter for SmartPDF AI."""
from typing import Optional

from services.llm_service import LLMServiceError, SYSTEM_INSTRUCTION, generate_llm_response


def generate_answer(
    context: str,
    question: str,
    model: Optional[str] = None,
    timeout: Optional[int] = None,
) -> str:
    """Generate a RAG answer with Groq Cloud."""
    if not isinstance(context, str) or not context.strip():
        raise LLMServiceError("The RAG context cannot be empty.", "empty_context", 400)
    if not isinstance(question, str) or not question.strip():
        raise LLMServiceError("The question cannot be empty.", "empty_question", 400)

    prompt = f"{SYSTEM_INSTRUCTION}\n\nContext:\n{context}\nQuestion:\n{question.strip()}"
    return generate_llm_response(prompt, model=model, timeout=timeout)
