"""General API health routes."""

from flask import Blueprint, jsonify, request

from services.llm_service import LLMServiceError, generate_llm_response

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    """Expose a simple health check endpoint."""
    return jsonify({"status": "ok", "service": "SmartPDF AI"})


@api_bp.post("/test-llm")
def test_llm():
    """Send a temporary prompt to the local Ollama backend."""
    payload = request.get_json(silent=True) or {}
    # parsed payload is available as `payload`
    prompt = (payload.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"error": "Prompt cannot be empty.", "code": "empty_prompt"}), 400

    try:
        response_text = generate_llm_response(prompt)
    except LLMServiceError as exc:
        return jsonify({"error": str(exc), "code": exc.code}), exc.status_code

    return jsonify({"response": response_text})
