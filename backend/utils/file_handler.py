"""File storage helpers."""

from pathlib import Path

from werkzeug.utils import secure_filename


def save_uploaded_file(file_storage, destination):
    """Save a Werkzeug upload object to the destination directory."""
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)

    filename = secure_filename(file_storage.filename)
    saved_path = destination / filename
    file_storage.save(saved_path)
    return saved_path
