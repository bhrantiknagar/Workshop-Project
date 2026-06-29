"""PDF upload routes."""

from flask import Blueprint, current_app, jsonify, request

from services.pdf_service import save_pdf
from utils.validator import validate_pdf_upload

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")


@upload_bp.post("")
def upload_pdf():
    """Validate and store an uploaded PDF."""
    file = request.files.get("pdf")
    is_valid, message = validate_pdf_upload(file, current_app.config)

    if not is_valid:
        return jsonify({"success": False, "message": message}), 400

    result = save_pdf(file, current_app.config["UPLOAD_FOLDER"])
    return jsonify(result), 201
