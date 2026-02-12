"""Application metrics collection for callback timing, data loading, and cache efficiency.

Provides a lightweight in-process metrics registry. Metrics are exposed via
the /metrics endpoint as JSON for scraping by Prometheus (via json_exporter),
Datadog, or custom monitoring.
"""

import threading
import time

from flask import jsonify

from app.logging_config import get_logger

logger = get_logger(__name__)

_lock = threading.Lock()

# Metrics storage
_counters = {}
_histograms = {}


def increment(name, value=1, labels=None):
    """Increment a counter metric.

    Args:
        name: Metric name (e.g. "cache_hits").
        value: Amount to increment by.
        labels: Optional dict of label key-value pairs.
    """
    key = _make_key(name, labels)
    with _lock:
        _counters[key] = _counters.get(key, 0) + value


def observe(name, duration, labels=None):
    """Record a timing observation in a histogram.

    Args:
        name: Metric name (e.g. "callback_duration_seconds").
        duration: Duration in seconds.
        labels: Optional dict of label key-value pairs.
    """
    key = _make_key(name, labels)
    with _lock:
        if key not in _histograms:
            _histograms[key] = {"count": 0, "sum": 0.0, "min": float("inf"), "max": 0.0}
        h = _histograms[key]
        h["count"] += 1
        h["sum"] += duration
        h["min"] = min(h["min"], duration)
        h["max"] = max(h["max"], duration)


def timer(name, labels=None):
    """Context manager that measures and records execution time.

    Usage:
        with metrics.timer("callback_duration_seconds", {"callback": "render_tab"}):
            do_work()
    """
    return _Timer(name, labels)


class _Timer:
    def __init__(self, name, labels):
        self._name = name
        self._labels = labels
        self._start = None

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        duration = time.perf_counter() - self._start
        observe(self._name, duration, self._labels)


def get_metrics():
    """Return a snapshot of all collected metrics."""
    with _lock:
        counters_out = {}
        for key, value in _counters.items():
            counters_out[key] = value

        histograms_out = {}
        for key, hist in _histograms.items():
            h = dict(hist)
            if h["count"] > 0:
                h["avg"] = round(h["sum"] / h["count"], 6)
            else:
                h["avg"] = 0.0
            h["sum"] = round(h["sum"], 6)
            h["min"] = round(h["min"], 6) if h["min"] != float("inf") else 0.0
            h["max"] = round(h["max"], 6)
            histograms_out[key] = h

        return {"counters": counters_out, "histograms": histograms_out}


def reset():
    """Reset all metrics. Primarily for testing."""
    with _lock:
        _counters.clear()
        _histograms.clear()


def _make_key(name, labels):
    """Build a metric key from name and labels."""
    if not labels:
        return name
    label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
    return f"{name}{{{label_str}}}"


def register_metrics_endpoint(server):
    """Register the /metrics endpoint on the Flask server.

    Args:
        server: The Flask server instance.
    """

    @server.route("/metrics")
    def metrics_endpoint():
        return jsonify(get_metrics())
