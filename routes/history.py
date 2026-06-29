"""History routes for prior uploads and conversations."""

from flask import Blueprint, jsonify

from services.history_service import list_history

history_bp = Blueprint("history", __name__, url_prefix="/history")


@history_bp.get("")
def history():
    """Return placeholder conversation history."""
    return jsonify({"items": list_history()})
