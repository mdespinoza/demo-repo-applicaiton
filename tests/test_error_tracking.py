"""Tests for the error tracking integration pattern."""

import pytest

from app import metrics
from app.error_tracking import capture_exception, capture_message, init_error_tracking


@pytest.fixture(autouse=True)
def reset_metrics_fixture():
    """Reset metrics before each test."""
    metrics.reset()
    yield
    metrics.reset()


class TestErrorTrackingWithoutSentry:
    """Tests for error tracking in log-only mode (no Sentry DSN)."""

    def test_init_without_sentry_dsn(self, monkeypatch):
        monkeypatch.delenv("SENTRY_DSN", raising=False)
        init_error_tracking()
        # Should not raise, should fall back to logging

    def test_capture_exception_increments_counter(self):
        try:
            raise RuntimeError("test error")
        except RuntimeError:
            capture_exception()

        data = metrics.get_metrics()
        assert data["counters"]["errors_total"] == 1

    def test_capture_exception_with_no_active_exception(self):
        # Should not raise even when there's no active exception
        capture_exception()
        data = metrics.get_metrics()
        assert data["counters"]["errors_total"] == 1

    def test_capture_message_does_not_raise(self):
        # Should log without error
        capture_message("Test warning", level="warning")
        capture_message("Test info", level="info")

    def test_multiple_exceptions_increment_counter(self):
        for i in range(3):
            try:
                raise ValueError(f"error {i}")
            except ValueError:
                capture_exception()

        data = metrics.get_metrics()
        assert data["counters"]["errors_total"] == 3
