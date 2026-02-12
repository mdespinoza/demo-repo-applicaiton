"""Structured logging configuration for the dashboard application.

Supports two output formats controlled by DASH_LOG_FORMAT env var:
  - "json"  : JSON lines for ELK/Splunk ingestion (default in production)
  - "text"  : Human-readable pipe-delimited format (default in development)
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Log file path — next to the app directory
LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app.log",
)

# Max log file size: 10 MB, keep 5 backups
LOG_MAX_BYTES = 10 * 1024 * 1024
LOG_BACKUP_COUNT = 5


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON for ELK/Splunk ingestion."""

    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S.") + f"{record.msecs:03.0f}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info and record.exc_info[0] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include any extra fields attached to the record
        for key in ("request_id", "duration_ms", "status_code", "endpoint", "component"):
            value = getattr(record, key, None)
            if value is not None:
                log_entry[key] = value

        return json.dumps(log_entry, default=str)


class TextFormatter(logging.Formatter):
    """Human-readable pipe-delimited format for development."""

    def __init__(self):
        super().__init__(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(level=None, log_format=None):
    """Configure application-wide logging.

    Args:
        level: Explicit log level. If None, reads from DASH_LOG_LEVEL
               environment variable, defaulting to DEBUG in dev and
               WARNING in production.
        log_format: "json" or "text". If None, reads from DASH_LOG_FORMAT
                    env var (defaults to "json" in production, "text" in dev).

    Returns:
        The root application logger ('app').
    """
    if level is None:
        from app.settings import DASH_LOG_LEVEL

        level = getattr(logging, DASH_LOG_LEVEL.upper(), logging.DEBUG)

    if log_format is None:
        from app.settings import DASH_ENV

        log_format = os.environ.get("DASH_LOG_FORMAT", "json" if DASH_ENV == "production" else "text")

    # Select formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        mode="a",
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Configure the application root logger
    logger = logging.getLogger("app")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("dash").setLevel(logging.WARNING)

    return logger


def get_logger(name):
    """Get a child logger under the 'app' namespace.

    Usage in any module:
        from app.logging_config import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")

    Args:
        name: Module name, typically __name__

    Returns:
        A logging.Logger instance as a child of 'app'.
    """
    return logging.getLogger(f"app.{name}")
