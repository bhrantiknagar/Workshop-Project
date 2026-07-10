"""Shared Groq LLM helpers."""

import os
from typing import Optional

from flask import current_app, has_app_context
from langchain_groq import ChatGroq

from config import Config

SYSTEM_INSTRUCTION = (
    "You are SmartPDF AI. Answer ONLY using the provided PDF context. "
    "Format answers for readability: use short paragraphs, numbered lists, "
    "or bullet points when listing details. Put each list item on its own line. "
    "If the answer cannot be found in the provided context, reply:\n"
    "I couldn't find that information in the uploaded PDF."
)


class LLMServiceError(Exception):
    """Raised when an LLM request cannot be completed."""

    def __init__(self, message: str, code: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def _resolve_model(model: Optional[str] = None) -> str:
    """Resolve the Groq model from the provided value or application config."""
    if model is not None:
        candidate = model.strip()
    elif has_app_context():
        candidate = current_app.config.get("GROQ_MODEL", Config.GROQ_MODEL)
    else:
        candidate = Config.GROQ_MODEL

    candidate = candidate.strip() if isinstance(candidate, str) else ""
    if not candidate:
        raise LLMServiceError(
            "The Groq model name is required.",
            "missing_model",
            400,
        )
    return candidate


def _resolve_api_key() -> str:
    api_key = current_app.config.get("GROQ_API_KEY", "") if has_app_context() else Config.GROQ_API_KEY
    api_key = api_key or os.getenv("GROQ_API_KEY", "")
    api_key = api_key.strip() if isinstance(api_key, str) else ""
    if not api_key:
        raise LLMServiceError("Groq API key is missing. Add GROQ_API_KEY to your environment.", "missing_groq_api_key", 400)
    return api_key


def generate_llm_response(prompt: str, model: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Send a prompt to Groq through LangChain and return the generated text."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise LLMServiceError("The prompt cannot be empty.", "empty_prompt", 400)

    resolved_timeout = timeout if timeout is not None else (
        current_app.config.get("GROQ_TIMEOUT", Config.GROQ_TIMEOUT) if has_app_context() else Config.GROQ_TIMEOUT
    )
    try:
        client = ChatGroq(
            api_key=_resolve_api_key(),
            model=_resolve_model(model),
            timeout=resolved_timeout,
            temperature=0.2,
        )
        response = client.invoke(prompt.strip())
    except LLMServiceError:
        raise
    except Exception as exc:
        raise LLMServiceError("Groq could not generate a response.", "groq_error", 502) from exc

    response_text = str(response.content or "").strip()
    if not response_text:
        raise LLMServiceError("Groq returned an empty response.", "empty_response", 502)

    return response_text


def answer_question(question: str, model: Optional[str] = None, timeout: int = 30) -> str:
    """Return an answer for a question using the configured Groq model."""
    return generate_llm_response(question, model=model, timeout=timeout)
