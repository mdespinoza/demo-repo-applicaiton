"""Environment-based application settings.

Reads configuration from environment variables with sensible defaults.
Supports .env files via manual loading (no extra dependencies required).
"""

import os

# ---------------------------------------------------------------------------
# .env file loading (lightweight, no dependency on python-dotenv)
# ---------------------------------------------------------------------------

_ENV_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")


def _load_dotenv(path=_ENV_FILE):
    """Load key=value pairs from a .env file into os.environ.

    Skips blank lines, comments (#), and lines without '='.
    Does NOT override variables already set in the environment.
    """
    if not os.path.isfile(path):
        return
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip("'\"")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()

# ---------------------------------------------------------------------------
# Settings — all sourced from environment with safe defaults
# ---------------------------------------------------------------------------

DASH_ENV = os.environ.get("DASH_ENV", "development")

# Server
DASH_HOST = os.environ.get("DASH_HOST", "127.0.0.1")
DASH_PORT = int(os.environ.get("DASH_PORT", "8050"))
DASH_DEBUG = os.environ.get("DASH_DEBUG", str(DASH_ENV == "development")).lower() in ("true", "1", "yes")

# Logging
DASH_LOG_LEVEL = os.environ.get("DASH_LOG_LEVEL", "DEBUG" if DASH_ENV == "development" else "WARNING")

# Gunicorn (used in production via gunicorn.conf.py or CLI)
GUNICORN_WORKERS = int(os.environ.get("GUNICORN_WORKERS", "4"))
GUNICORN_TIMEOUT = int(os.environ.get("GUNICORN_TIMEOUT", "120"))
