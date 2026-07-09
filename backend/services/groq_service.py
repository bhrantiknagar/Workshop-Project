"""Groq provider adapter for SmartPDF AI."""

import os
from typing import Optional

from flask import current_app, has_app_context

from config import Config
from services.llm_service import LLMServiceError
from services.ollama_service import SYSTEM_INSTRUCTION


def _get_config_value(name: str, default=None):
    """Read config from Flask when available, otherwise from Config."""
    if has_app_context():
        return current_app.config.get(name, default)
    return getattr(Config, name, default)


def _resolve_api_key() -> str:
    api_key = _get_config_value("GROQ_API_KEY") or os.getenv("GROQ_API_KEY", "")
    api_key = api_key.strip() if isinstance(api_key, str) else ""
    if not api_key:
        raise LLMServiceError(
            "Groq API key is missing. Add GROQ_API_KEY to your .env file.",
            "missing_groq_api_key",
            400,
        )
    return api_key


def _resolve_model(model: Optional[str] = None) -> str:
    candidate = model or _get_config_value("GROQ_MODEL", Config.GROQ_MODEL)
    candidate = candidate.strip() if isinstance(candidate, str) else ""
    if not candidate:
        raise LLMServiceError("The Groq model name is required.", "missing_model", 400)
    return candidate


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

    try:
        from groq import APIConnectionError, APIStatusError, APITimeoutError, Groq
    except ImportError as exc:
        raise LLMServiceError(
            "The Groq SDK is not installed. Run `pip install groq`.",
            "groq_sdk_missing",
            500,
        ) from exc

    resolved_timeout = timeout or _get_config_value("GROQ_TIMEOUT", Config.GROQ_TIMEOUT)
    client = Groq(api_key=_resolve_api_key(), timeout=resolved_timeout)

    try:
        completion = client.chat.completions.create(
            model=_resolve_model(model),
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {
                    "role": "user",
                    "content": f"Context:\n{context}\nQuestion:\n{question.strip()}",
                },
            ],
            temperature=0.2,
        )
    except APITimeoutError as exc:
        raise LLMServiceError("The request to Groq timed out.", "timeout", 504) from exc
    except APIConnectionError as exc:
        raise LLMServiceError(
            "Unable to connect to Groq. Check your internet connection.",
            "groq_unavailable",
            503,
        ) from exc
    except APIStatusError as exc:
        detail = getattr(exc, "message", str(exc))
        raise LLMServiceError(
            f"Groq returned an API error: {detail}",
            "groq_error",
            exc.status_code,
        ) from exc
    except Exception as exc:
        raise LLMServiceError("Groq could not generate an answer.", "groq_error", 502) from exc

    response_text = (completion.choices[0].message.content or "").strip()
    if not response_text:
        raise LLMServiceError("Groq returned an empty response.", "empty_response", 502)

    return response_text
