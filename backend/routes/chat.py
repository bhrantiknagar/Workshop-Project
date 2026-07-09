"""Chat question routes."""

from flask import Blueprint, jsonify, request

from services.llm_service import LLMServiceError
from services.rag_service import answer_with_rag

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.post("/ask")
def ask_question():
    """Return an answer for a user question."""
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "").strip()
    pdf_ids = payload.get("pdf_ids") or None
    provider = payload.get("provider") or "groq"

    if not question:
        return jsonify({"answer": "Please enter a question."}), 400

    try:
        result = answer_with_rag(question, pdf_ids=pdf_ids, provider=provider)
    except LLMServiceError as exc:
        return jsonify({"answer": str(exc)}), exc.status_code
    except Exception as exc:
        # If retrieval failed, present a helpful message
        return jsonify({"answer": str(exc)}), 500

    return jsonify(
        {
            "answer": result.get("answer", ""),
            "provider": result.get("provider", provider),
            "provider_label": result.get("provider_label", "Groq Cloud"),
            "sources": result.get("sources", []),
        }
    )
