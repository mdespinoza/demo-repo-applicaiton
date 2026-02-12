"""Error tracking integration pattern (Sentry-compatible).

Provides a pluggable error tracking interface. When a DSN is configured
(SENTRY_DSN env var), it initializes the Sentry SDK. Otherwise, errors
are captured via structured logging — no external dependency required.

Usage:
    from app.error_tracking import capture_exception, capture_message

    try:
        risky_operation()
    except Exception:
        capture_exception()  # logs or sends to Sentry

    capture_message("Unusual condition detected", level="warning")
"""

import os
import sys

from app.logging_config import get_logger
from app import metrics

logger = get_logger(__name__)

_sentry_initialized = False


def init_error_tracking():
    """Initialize error tracking.

    If SENTRY_DSN is set, initializes the Sentry SDK.
    Otherwise, falls back to structured logging.
    """
    global _sentry_initialized
    dsn = os.environ.get("SENTRY_DSN", "")

    if dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=dsn,
                environment=os.environ.get("DASH_ENV", "development"),
                traces_sample_rate=float(os.environ.get("SENTRY_TRACES_RATE", "0.1")),
            )
            _sentry_initialized = True
            logger.info("Sentry error tracking initialized")
        except ImportError:
            logger.warning("SENTRY_DSN is set but sentry-sdk is not installed; using log-based tracking")
    else:
        logger.info("Error tracking using structured logging (set SENTRY_DSN to enable Sentry)")


def capture_exception(exc_info=None):
    """Capture an exception for error tracking.

    Args:
        exc_info: Exception info tuple (type, value, traceback).
                  If None, uses sys.exc_info().
    """
    if exc_info is None:
        exc_info = sys.exc_info()

    metrics.increment("errors_total")

    if _sentry_initialized:
        try:
            import sentry_sdk

            sentry_sdk.capture_exception(exc_info[1] if exc_info[1] else None)
        except Exception:
            logger.error("Failed to send exception to Sentry", exc_info=True)
    else:
        if exc_info[0] is not None:
            logger.error(
                "Exception captured: %s: %s",
                exc_info[0].__name__,
                exc_info[1],
                exc_info=exc_info,
            )


def capture_message(message, level="info"):
    """Capture an informational message for error tracking.

    Args:
        message: The message string.
        level: Log level ("debug", "info", "warning", "error", "fatal").
    """
    if _sentry_initialized:
        try:
            import sentry_sdk

            sentry_sdk.capture_message(message, level=level)
        except Exception:
            logger.error("Failed to send message to Sentry", exc_info=True)
    else:
        log_fn = getattr(logger, level, logger.info)
        log_fn("Error tracking message: %s", message)
