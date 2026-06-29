"""General API health routes."""

from flask import Blueprint, jsonify

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.get("/health")
def health():
    """Expose a simple health check endpoint."""
    return jsonify({"status": "ok", "service": "SmartPDF AI"})
