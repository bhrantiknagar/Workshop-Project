"""PDF storage and extraction service placeholders."""

from pathlib import Path

from utils.file_handler import save_uploaded_file


def save_pdf(file_storage, upload_folder):
    """Save an uploaded PDF and return metadata for the UI."""
    saved_path = save_uploaded_file(file_storage, Path(upload_folder))
    return {
        "success": True,
        "message": "PDF uploaded successfully. AI processing is not implemented yet.",
        "filename": saved_path.name,
    }


def extract_text(pdf_path):
    """Extract text from a PDF with PyMuPDF.

    TODO: Implement PyMuPDF text extraction.
    """
    return ""
