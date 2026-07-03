"""Helpers for communicating with a local Ollama model."""

import json
import socket
from typing import Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import has_app_context, current_app

from config import Config


class LLMServiceError(Exception):
    """Raised when the Ollama request cannot be completed."""

    def __init__(self, message: str, code: str, status_code: int = 500):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code


def _resolve_model(model: Optional[str] = None) -> str:
    """Resolve the Ollama model from the provided value or application config."""
    if model is not None:
        candidate = model.strip()
    elif has_app_context():
        # prefer MODEL_NAME (new config) falling back to legacy OLLAMA_MODEL
        candidate = current_app.config.get("MODEL_NAME", current_app.config.get("OLLAMA_MODEL", Config.OLLAMA_MODEL))
    else:
        candidate = Config.MODEL_NAME if hasattr(Config, "MODEL_NAME") else Config.OLLAMA_MODEL

    candidate = candidate.strip() if isinstance(candidate, str) else ""
    if not candidate:
        raise LLMServiceError(
            "The Ollama model name is required.",
            "missing_model",
            400,
        )
    return candidate


def generate_llm_response(prompt: str, model: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """Send a prompt to Ollama and return the generated response."""
    if not isinstance(prompt, str) or not prompt.strip():
        raise LLMServiceError("The prompt cannot be empty.", "empty_prompt", 400)

    if timeout is None:
        timeout = (
            current_app.config.get("OLLAMA_TIMEOUT")
            if has_app_context()
            else Config.OLLAMA_TIMEOUT
        )

    resolved_model = _resolve_model(model)
    base_url = Config.OLLAMA_BASE_URL.rstrip("/")
    url = f"{base_url}/api/generate"
    payload = {
        "model": resolved_model,
        "prompt": prompt.strip(),
        "stream": False,
    }

    try:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            data = json.loads(body)
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        if exc.code == 404 and ":" not in resolved_model:
            fallback_model = f"{resolved_model}:latest"
            payload["model"] = fallback_model
            try:
                fallback_request = Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )
                with urlopen(fallback_request, timeout=timeout) as response:
                    body = response.read().decode("utf-8")
                    data = json.loads(body)
            except HTTPError:
                raise LLMServiceError(
                    f"The requested Ollama model '{fallback_model}' was not found. Pull it with `ollama pull {fallback_model}`.",
                    "missing_model",
                    404,
                ) from exc
        elif exc.code == 404:
            raise LLMServiceError(
                f"The requested Ollama model '{resolved_model}' was not found. Pull it with `ollama pull {resolved_model}`.",
                "missing_model",
                404,
            ) from exc
        else:
            raise LLMServiceError(
                f"Ollama returned an HTTP error: {detail or exc.reason}",
                "ollama_error",
                exc.code,
            ) from exc
    except URLError as exc:
        reason = getattr(exc, "reason", exc)
        raise LLMServiceError(
            "Unable to connect to Ollama. Make sure the Ollama service is running.",
            "ollama_unavailable",
            503,
        ) from reason
    except socket.timeout as exc:
        raise LLMServiceError("The request to Ollama timed out.", "timeout", 504) from exc
    except (ValueError, TypeError) as exc:
        raise LLMServiceError("Ollama returned an invalid response.", "invalid_response", 502) from exc

    response_text = (data.get("response") or "").strip()
    if not response_text:
        raise LLMServiceError("Ollama returned an empty response.", "empty_response", 502)

    return response_text


def answer_question(question: str, model: Optional[str] = None, timeout: int = 30) -> str:
    """Return an answer for a question using the configured Ollama model."""
    return generate_llm_response(question, model=model, timeout=timeout)
