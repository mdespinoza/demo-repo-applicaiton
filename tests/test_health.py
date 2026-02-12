"""Tests for the health check endpoint."""

import json

import pytest


@pytest.fixture
def client():
    """Create a Flask test client from the Dash app's server."""
    from app.main import server

    server.config["TESTING"] = True
    with server.test_client() as client:
        yield client


class TestHealthEndpoint:
    """Tests for the /health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_json(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert "status" in data
        assert "uptime_seconds" in data
        assert "cache" in data

    def test_health_status_field(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["status"] in ("healthy", "degraded")

    def test_health_uptime_positive(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert data["uptime_seconds"] >= 0

    def test_health_cache_section(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        cache = data["cache"]
        for dataset in ("equipment", "bases", "healthcare", "ecg"):
            assert dataset in cache
            assert "exists" in cache[dataset]
            assert "size_bytes" in cache[dataset]

    def test_health_data_available_field(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert "data_available" in data
        assert isinstance(data["data_available"], bool)

    def test_health_all_caches_warm_field(self, client):
        response = client.get("/health")
        data = json.loads(response.data)
        assert "all_caches_warm" in data
        assert isinstance(data["all_caches_warm"], bool)
