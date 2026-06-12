"""Tests for the /chat endpoint."""

from unittest.mock import AsyncMock

from openai import AuthenticationError, RateLimitError, APIConnectionError


class TestChatCompletion:
    """Tests for POST /chat."""

    VALID_PAYLOAD = {
        "messages": [{"role": "user", "content": "Hello!"}],
    }

    def test_returns_200_with_valid_request(self, client):
        response = client.post("/chat", json=self.VALID_PAYLOAD)
        assert response.status_code == 200

    def test_response_is_openai_compatible(self, client):
        response = client.post("/chat", json=self.VALID_PAYLOAD)
        data = response.json()

        # Verify OpenAI-compatible response structure
        assert "id" in data
        assert data["object"] == "chat.completion"
        assert "created" in data
        assert "model" in data
        assert "choices" in data
        assert "usage" in data

        # Verify choice structure
        choice = data["choices"][0]
        assert "message" in choice
        assert choice["message"]["role"] == "assistant"
        assert choice["message"]["content"]  # not empty
        assert "finish_reason" in choice

        # Verify usage structure
        usage = data["usage"]
        assert "prompt_tokens" in usage
        assert "completion_tokens" in usage
        assert "total_tokens" in usage

    def test_includes_request_id_in_response(self, client):
        response = client.post("/chat", json=self.VALID_PAYLOAD)
        assert "x-request-id" in response.headers

    def test_custom_model_is_passed_through(self, client):
        payload = {
            **self.VALID_PAYLOAD,
            "model": "gpt-4o",
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200

    def test_temperature_and_max_tokens(self, client):
        payload = {
            **self.VALID_PAYLOAD,
            "temperature": 0.0,
            "max_tokens": 100,
        }
        response = client.post("/chat", json=payload)
        assert response.status_code == 200


class TestChatValidation:
    """Tests for request validation on /chat."""

    def test_missing_messages_returns_422(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422

    def test_empty_messages_returns_422(self, client):
        response = client.post("/chat", json={"messages": []})
        assert response.status_code == 422

    def test_invalid_role_returns_422(self, client):
        response = client.post(
            "/chat",
            json={"messages": [{"role": "invalid", "content": "Hello"}]},
        )
        assert response.status_code == 422

    def test_empty_content_returns_422(self, client):
        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": ""}]},
        )
        assert response.status_code == 422

    def test_temperature_out_of_range_returns_422(self, client):
        response = client.post(
            "/chat",
            json={
                "messages": [{"role": "user", "content": "Hi"}],
                "temperature": 3.0,
            },
        )
        assert response.status_code == 422

    def test_stream_true_returns_501(self, client):
        response = client.post(
            "/chat",
            json={
                "messages": [{"role": "user", "content": "Hi"}],
                "stream": True,
            },
        )
        assert response.status_code == 501


class TestChatErrorHandling:
    """Tests for LLM provider error handling."""

    def _make_mock_response(self):
        """Create a minimal mock httpx.Response for OpenAI errors."""
        from unittest.mock import MagicMock

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.headers = {}
        mock_resp.request = MagicMock()
        mock_resp.request.url = "https://api.openai.com/v1/chat/completions"
        mock_resp.request.method = "POST"
        mock_resp.request.headers = {}
        return mock_resp

    def test_auth_error_returns_401(self, client):
        mock_service = AsyncMock()
        mock_resp = self._make_mock_response()
        mock_resp.status_code = 401
        mock_service.chat.side_effect = AuthenticationError(
            message="Invalid API key",
            response=mock_resp,
            body={"error": {"message": "Invalid API key"}},
        )
        client.app.state.llm_service = mock_service

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
        assert response.status_code == 401

    def test_rate_limit_returns_429(self, client):
        mock_service = AsyncMock()
        mock_resp = self._make_mock_response()
        mock_resp.status_code = 429
        mock_resp.headers = {"retry-after": "1"}
        mock_service.chat.side_effect = RateLimitError(
            message="Rate limit exceeded",
            response=mock_resp,
            body={"error": {"message": "Rate limit exceeded"}},
        )
        client.app.state.llm_service = mock_service

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
        assert response.status_code == 429

    def test_connection_error_returns_502(self, client):
        mock_service = AsyncMock()
        mock_service.chat.side_effect = APIConnectionError(
            request=self._make_mock_response().request,
        )
        client.app.state.llm_service = mock_service

        response = client.post(
            "/chat",
            json={"messages": [{"role": "user", "content": "Hi"}]},
        )
        assert response.status_code == 502
