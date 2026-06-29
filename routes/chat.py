"""Chat question routes."""

from flask import Blueprint, jsonify, request

from services.llm_service import answer_question

chat_bp = Blueprint("chat", __name__, url_prefix="/chat")


@chat_bp.post("/ask")
def ask_question():
    """Return an answer for a user question."""
    payload = request.get_json(silent=True) or {}
    question = payload.get("question", "").strip()

    if not question:
        return jsonify({"answer": "Please enter a question."}), 400

    answer = answer_question(question)
    return jsonify({"answer": answer})
