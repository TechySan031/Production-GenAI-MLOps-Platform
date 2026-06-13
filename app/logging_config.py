"""Structured logging configuration.

JSON format for production (Azure Monitor / Log Analytics indexable).
Human-readable text format for local development.
"""

import logging
import sys
from typing import Any

from pythonjsonlogger.json import JsonFormatter

from app.config import get_settings


def setup_logging() -> None:
    """Configure application logging based on settings."""
    settings = get_settings()

    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL.upper())

    # Clear any existing handlers to avoid duplicate log lines
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)

    formatter: Any

    if settings.LOG_FORMAT == "json":
        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
                "name": "logger",
            },
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)