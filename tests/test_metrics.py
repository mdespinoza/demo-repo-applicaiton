"""Tests for the application metrics collection module."""

import json
import time

import pytest

from app import metrics


@pytest.fixture(autouse=True)
def reset_metrics():
    """Reset metrics before each test."""
    metrics.reset()
    yield
    metrics.reset()


class TestCounters:
    """Tests for counter metrics."""

    def test_increment_default(self):
        metrics.increment("requests")
        data = metrics.get_metrics()
        assert data["counters"]["requests"] == 1

    def test_increment_by_value(self):
        metrics.increment("bytes_sent", value=1024)
        data = metrics.get_metrics()
        assert data["counters"]["bytes_sent"] == 1024

    def test_increment_multiple_times(self):
        metrics.increment("hits")
        metrics.increment("hits")
        metrics.increment("hits")
        data = metrics.get_metrics()
        assert data["counters"]["hits"] == 3

    def test_increment_with_labels(self):
        metrics.increment("cache_hits", labels={"dataset": "equipment", "layer": "memory"})
        metrics.increment("cache_hits", labels={"dataset": "bases", "layer": "parquet"})
        data = metrics.get_metrics()
        assert data["counters"]["cache_hits{dataset=equipment,layer=memory}"] == 1
        assert data["counters"]["cache_hits{dataset=bases,layer=parquet}"] == 1


class TestHistograms:
    """Tests for histogram (timing) metrics."""

    def test_observe_single(self):
        metrics.observe("load_time", 0.5)
        data = metrics.get_metrics()
        hist = data["histograms"]["load_time"]
        assert hist["count"] == 1
        assert hist["sum"] == pytest.approx(0.5, abs=1e-4)
        assert hist["min"] == pytest.approx(0.5, abs=1e-4)
        assert hist["max"] == pytest.approx(0.5, abs=1e-4)

    def test_observe_multiple(self):
        metrics.observe("load_time", 0.1)
        metrics.observe("load_time", 0.3)
        metrics.observe("load_time", 0.2)
        data = metrics.get_metrics()
        hist = data["histograms"]["load_time"]
        assert hist["count"] == 3
        assert hist["sum"] == pytest.approx(0.6, abs=1e-4)
        assert hist["min"] == pytest.approx(0.1, abs=1e-4)
        assert hist["max"] == pytest.approx(0.3, abs=1e-4)
        assert hist["avg"] == pytest.approx(0.2, abs=1e-4)

    def test_observe_with_labels(self):
        metrics.observe("callback_time", 0.05, labels={"callback": "render_tab"})
        data = metrics.get_metrics()
        key = "callback_time{callback=render_tab}"
        assert key in data["histograms"]


class TestTimer:
    """Tests for the timer context manager."""

    def test_timer_records_duration(self):
        with metrics.timer("operation_seconds"):
            time.sleep(0.01)

        data = metrics.get_metrics()
        hist = data["histograms"]["operation_seconds"]
        assert hist["count"] == 1
        assert hist["sum"] > 0

    def test_timer_with_labels(self):
        with metrics.timer("op_seconds", {"type": "read"}):
            pass

        data = metrics.get_metrics()
        assert "op_seconds{type=read}" in data["histograms"]


class TestReset:
    """Tests for the reset function."""

    def test_reset_clears_all(self):
        metrics.increment("counter_a")
        metrics.observe("hist_a", 1.0)
        metrics.reset()
        data = metrics.get_metrics()
        assert data["counters"] == {}
        assert data["histograms"] == {}


class TestMetricsEndpoint:
    """Tests for the /metrics Flask endpoint."""

    @pytest.fixture
    def client(self):
        from app.main import server

        server.config["TESTING"] = True
        with server.test_client() as client:
            yield client

    def test_metrics_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_returns_json(self, client):
        response = client.get("/metrics")
        data = json.loads(response.data)
        assert "counters" in data
        assert "histograms" in data
