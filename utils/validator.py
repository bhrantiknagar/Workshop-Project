"""Request and file validation helpers."""


def allowed_file(filename, allowed_extensions):
    """Check whether a filename uses an allowed extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def validate_pdf_upload(file_storage, config):
    """Validate an uploaded PDF file before storage."""
    if file_storage is None or file_storage.filename == "":
        return False, "No PDF file was selected."

    if not allowed_file(file_storage.filename, config["ALLOWED_EXTENSIONS"]):
        return False, "Only PDF files are allowed."

    return True, "PDF is valid."
