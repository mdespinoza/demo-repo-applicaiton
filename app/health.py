"""Health check endpoint for monitoring and load balancer integration.

Registers a /health route on the Flask server underlying the Dash app.
Returns JSON status of application, cache, and data availability.
"""

import os
import time

from flask import jsonify

from app.config import CACHE_DIR, ECG_CACHE, EQUIPMENT_CACHE, BASES_CACHE, HEALTHCARE_CACHE
from app.logging_config import get_logger

logger = get_logger(__name__)

# Track application start time
_start_time = time.time()


def register_health_endpoint(server):
    """Register the /health endpoint on the Flask server.

    Args:
        server: The Flask server instance (app.server from Dash).
    """

    @server.route("/health")
    def health_check():
        uptime_seconds = time.time() - _start_time

        # Check cache status
        cache_files = {
            "equipment": EQUIPMENT_CACHE,
            "bases": BASES_CACHE,
            "healthcare": HEALTHCARE_CACHE,
            "ecg": ECG_CACHE,
        }
        cache_status = {}
        for name, path in cache_files.items():
            cache_status[name] = {
                "exists": os.path.exists(path),
                "size_bytes": os.path.getsize(path) if os.path.exists(path) else 0,
            }

        # Check data directory
        datasets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datasets")
        data_available = os.path.isdir(datasets_dir)

        # Determine overall health
        all_caches_exist = all(s["exists"] for s in cache_status.values())
        status = "healthy" if data_available else "degraded"

        response = {
            "status": status,
            "uptime_seconds": round(uptime_seconds, 1),
            "cache": cache_status,
            "cache_directory": os.path.exists(CACHE_DIR),
            "data_available": data_available,
            "all_caches_warm": all_caches_exist,
        }

        http_status = 200 if status == "healthy" else 503
        return jsonify(response), http_status
