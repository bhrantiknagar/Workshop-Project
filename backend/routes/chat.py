"""Chat question routes."""

from flask import Blueprint, jsonify, request

from services.comparison_service import compare_pdfs
from services.llm_service import LLMServiceError
from services.quick_action_service import run_quick_action
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


@chat_bp.post("/compare")
def compare_documents():
    """Compare two uploaded PDFs using the selected LLM provider."""
    payload = request.get_json(silent=True) or {}
    prompt = payload.get("prompt", "").strip()
    pdf_ids = payload.get("pdf_ids") or []
    provider = payload.get("provider") or "groq"

    if not prompt:
        return jsonify({"answer": "Please enter what you want to compare."}), 400

    if len(pdf_ids) != 2:
        return jsonify({"answer": "Upload exactly two PDFs before comparing."}), 400

    try:
        result = compare_pdfs(prompt, pdf_ids=pdf_ids, provider=provider)
    except LLMServiceError as exc:
        return jsonify({"answer": str(exc)}), exc.status_code
    except Exception as exc:
        return jsonify({"answer": str(exc)}), 500

    return jsonify(
        {
            "answer": result.get("answer", ""),
            "provider": result.get("provider", provider),
            "provider_label": result.get("provider_label", "Groq Cloud"),
            "sources": result.get("sources", {}),
        }
    )


@chat_bp.post("/action")
def run_action():
    """Run a predefined Quick AI Action through RAG."""
    payload = request.get_json(silent=True) or {}
    action = payload.get("action", "").strip()
    pdf_ids = payload.get("pdf_ids") or []
    provider = payload.get("provider") or "groq"

    if not action:
        return jsonify({"answer": "Choose a Quick AI Action first."}), 400

    if not pdf_ids:
        return jsonify({"answer": "Upload at least one PDF before using Quick AI Actions."}), 400

    try:
        result = run_quick_action(action, pdf_ids=pdf_ids, provider=provider)
    except LLMServiceError as exc:
        return jsonify({"answer": str(exc)}), exc.status_code
    except Exception as exc:
        return jsonify({"answer": str(exc)}), 500

    return jsonify(
        {
            "answer": result.get("answer", ""),
            "action": result.get("action", action),
            "action_label": result.get("action_label", "Quick AI Action"),
            "provider": result.get("provider", provider),
            "provider_label": result.get("provider_label", "Groq Cloud"),
            "sources": result.get("sources", []),
        }
    )
