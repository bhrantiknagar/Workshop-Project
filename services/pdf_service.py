"""PDF storage and extraction service helpers."""

from pathlib import Path

import fitz

from utils.file_handler import save_uploaded_file


def _format_file_size(size_bytes):
    """Return a readable file size string."""
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _count_pdf_pages(pdf_path):
    """Count pages in a PDF using PyMuPDF."""
    with fitz.open(pdf_path) as document:
        return document.page_count


class PDFProcessingError(Exception):
    """Raised when an uploaded PDF cannot be read safely."""


def _read_pdf_document(pdf_path):
    """Open and validate a PDF document with user-friendly errors."""
    try:
        document = fitz.open(pdf_path)
    except (fitz.FileDataError, fitz.EmptyFileError, RuntimeError) as error:
        raise PDFProcessingError("This PDF appears to be corrupted.") from error

    if document.needs_pass:
        document.close()
        raise PDFProcessingError("Password-protected PDFs are not supported yet.")

    if document.page_count == 0:
        document.close()
        raise PDFProcessingError("This PDF does not contain any pages.")

    return document


def _extract_pdf_data(pdf_path, filename, pdf_id):
    """Extract metadata and page-by-page text from a saved PDF."""
    size_bytes = Path(pdf_path).stat().st_size

    with _read_pdf_document(pdf_path) as document:
        metadata = document.metadata or {}
        pages = [
            {
                "page": page_number + 1,
                "text": document.load_page(page_number).get_text("text").strip(),
            }
            for page_number in range(document.page_count)
        ]

        return {
            "id": pdf_id,
            "filename": filename,
            "file_size": _format_file_size(size_bytes),
            "file_size_bytes": size_bytes,
            "total_pages": document.page_count,
            "metadata": {
                "title": metadata.get("title") or "",
                "author": metadata.get("author") or "",
            },
            "pages": pages,
            "status": "Ready",
        }


def save_pdf(file_storage, upload_folder, pdf_id="pdf_001"):
    """Save an uploaded PDF, then extract metadata and page text."""
    saved_path = save_uploaded_file(file_storage, Path(upload_folder))
    return _extract_pdf_data(saved_path, saved_path.name, pdf_id)


def save_pdfs(file_storages, upload_folder):
    """Save multiple uploaded PDFs and return metadata for each file."""
    files = [
        save_pdf(file_storage, upload_folder, f"pdf_{index:03d}")
        for index, file_storage in enumerate(file_storages, start=1)
    ]

    return {
        "success": True,
        "message": f"{len(files)} PDF{'s' if len(files) != 1 else ''} uploaded successfully.",
        "files": files,
    }


def extract_text(pdf_path):
    """Extract page-by-page text from a PDF path."""
    pdf_path = Path(pdf_path)
    return _extract_pdf_data(pdf_path, pdf_path.name, "pdf_001")["pages"]
