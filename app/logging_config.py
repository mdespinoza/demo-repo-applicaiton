"""Structured logging configuration for the dashboard application."""

import logging
import os
import sys

# Log file path — next to the app directory
LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "app.log",
)


def setup_logging(level=None):
    """Configure application-wide logging.

    Args:
        level: Explicit log level. If None, reads from DASH_LOG_LEVEL
               environment variable, defaulting to DEBUG in dev and
               WARNING in production.

    Returns:
        The root application logger ('app').
    """
    if level is None:
        from app.settings import DASH_LOG_LEVEL

        level = getattr(logging, DASH_LOG_LEVEL.upper(), logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_handler.setFormatter(fmt)

    # File handler (app.log)
    file_handler = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

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
