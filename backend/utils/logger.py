"""Logging configuration for Flask."""

import logging
from logging.handlers import RotatingFileHandler


def configure_logger(app):
    """Attach a rotating file logger to the Flask app."""
    log_file = app.config["LOG_FILE"]
    log_file.parent.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(log_file, maxBytes=1_000_000, backupCount=3)
    handler.setLevel(logging.INFO)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s: %(message)s")
    )

    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
