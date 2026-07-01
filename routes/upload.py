"""PDF upload routes."""

from flask import Blueprint, current_app, jsonify, request

from services.pdf_service import PDFProcessingError, save_pdfs
from utils.validator import validate_pdf_upload

upload_bp = Blueprint("upload", __name__, url_prefix="/upload")


@upload_bp.post("")
def upload_pdf():
    """Validate and store an uploaded PDF."""
    files = request.files.getlist("pdf")

    if not files or all(file.filename == "" for file in files):
        return jsonify({"success": False, "message": "No PDF file was selected."}), 400

    files = [file for file in files if file.filename]

    if len(files) > 3:
        return jsonify(
            {
                "success": False,
                "message": "Upload up to 3 PDF files only.",
            }
        ), 400

    for file in files:
        is_valid, message = validate_pdf_upload(file, current_app.config)

        if not is_valid:
            return jsonify({"success": False, "message": message}), 400

    try:
        result = save_pdfs(files, current_app.config["UPLOAD_FOLDER"])
    except PDFProcessingError as error:
        return jsonify(
            {
                "success": False,
                "message": str(error),
            }
        ), 400
    except Exception as error:
        current_app.logger.exception("PDF upload failed")
        return jsonify(
            {
                "success": False,
                "message": "Could not process one of the uploaded PDFs.",
            }
        ), 400

    return jsonify(result), 201
