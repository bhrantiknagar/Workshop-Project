"""Document summary routes."""

from flask import Blueprint, jsonify

from services.summary_service import generate_summary

summary_bp = Blueprint("summary", __name__, url_prefix="/summary")


@summary_bp.post("/generate")
def summary():
    """Return a placeholder summary for the active document."""
    return jsonify({"summary": generate_summary()})
