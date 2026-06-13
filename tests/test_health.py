"""Tests for health check endpoints."""

from unittest.mock import AsyncMock


class TestLiveness:
    """Tests for GET /health (liveness probe)."""

    def test_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_response_contains_status(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_response_contains_version(self, client):
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert data["version"]  # not empty

    def test_response_contains_environment(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["environment"] == "development"

    def test_includes_request_id_header(self, client):
        response = client.get("/health")
        assert "x-request-id" in response.headers

    def test_honors_client_request_id(self, client):
        custom_id = "my-trace-id-123"
        response = client.get("/health", headers={"x-request-id": custom_id})
        assert response.headers["x-request-id"] == custom_id


class TestReadiness:
    """Tests for GET /health/ready (readiness probe)."""

    def test_returns_200_when_healthy(self, client):
        response = client.get("/health/ready")
        assert response.status_code == 200

    def test_response_shows_ready_status(self, client):
        response = client.get("/health/ready")
        data = response.json()
        assert data["status"] == "ready"

    def test_response_includes_checks(self, client):
        response = client.get("/health/ready")
        data = response.json()
        assert "checks" in data
        assert data["checks"]["api_key_configured"] is True
        assert data["checks"]["llm_provider_healthy"] is True

    def test_returns_503_when_provider_unhealthy(self, client):
        # Override the mock to simulate an unhealthy provider
        mock_service = AsyncMock()
        mock_service.provider_name = "openai"
        mock_service.is_healthy.return_value = False
        client.app.state.llm_service = mock_service

        response = client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
