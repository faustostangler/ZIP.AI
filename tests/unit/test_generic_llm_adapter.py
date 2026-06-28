from datetime import UTC, datetime

import httpx

from src.adapters.generic_llm_adapter import GenericLLMAdapter
from src.domain.entities import Email


def test_generic_llm_adapter_is_newsletter_ollama(monkeypatch):
    # Setup settings overrides
    monkeypatch.setattr("src.config.settings.llm_provider", "ollama")
    monkeypatch.setattr("src.config.settings.ollama_base_url", "http://localhost:11434")
    monkeypatch.setattr("src.config.settings.ollama_model", "qwen2.5:7b")

    email = Email(
        id="111",
        thread_id="t111",
        subject="Weekly Marketing Newsletter",
        sender="promo@store.com",
        body="Buy one get one free this week only!",
        received_at=datetime.now(UTC),
    )

    mock_response_data = {"message": {"content": '{"is_newsletter": true}'}}

    # Mock httpx post
    class MockResponse:
        def __init__(self, json_data, status_code=200):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code >= 400:
                raise httpx.HTTPStatusError("Error", request=None, response=self)

    def mock_post(url, json, **kwargs):
        assert "http://localhost:11434/api/chat" in url
        # Ensure schema is requested in format property
        assert "format" in json
        assert json["format"]["properties"]["is_newsletter"]["type"] == "boolean"
        return MockResponse(mock_response_data)

    client = httpx.Client()
    monkeypatch.setattr(client, "post", mock_post)

    adapter = GenericLLMAdapter(client=client)
    res = adapter.is_newsletter_sender([email])

    assert res is True


def test_generic_llm_adapter_fallback_on_error(monkeypatch):
    monkeypatch.setattr("src.config.settings.llm_provider", "ollama")
    client = httpx.Client()

    def mock_post(url, json, **kwargs):
        raise httpx.RequestError("Connection refused")

    monkeypatch.setattr(client, "post", mock_post)

    adapter = GenericLLMAdapter(client=client)
    res = adapter.is_newsletter_sender([])
    assert res is False


def test_generic_llm_adapter_classify_email_ollama(monkeypatch):
    monkeypatch.setattr("src.config.settings.llm_provider", "ollama")
    monkeypatch.setattr("src.config.settings.ollama_base_url", "http://localhost:11434")
    monkeypatch.setattr("src.config.settings.ollama_model", "qwen2.5:7b")

    email = Email(
        id="111",
        thread_id="t111",
        subject="Invoice #456",
        sender="billing@cloud.com",
        body="Here is your invoice for this month.",
        received_at=datetime.now(UTC),
    )

    mock_response_data = {
        "message": {
            "content": '{"email_id": "111", "action": "archive", "label_to_add": null, "reason": "Monthly receipt", "is_commercial": false, "confidence": 0.95}'
        }
    }

    class MockResponse:
        def __init__(self, json_data):
            self.json_data = json_data

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass

    client = httpx.Client()
    monkeypatch.setattr(
        client, "post", lambda url, json, **kwargs: MockResponse(mock_response_data)
    )

    adapter = GenericLLMAdapter(client=client)
    res = adapter.classify_email(email)

    assert res.email_id == "111"
    assert res.action == "archive"
    assert res.is_commercial is False


def test_generic_llm_adapter_check_commercial_pattern_ollama(monkeypatch):
    monkeypatch.setattr("src.config.settings.llm_provider", "ollama")
    monkeypatch.setattr("src.config.settings.ollama_base_url", "http://localhost:11434")
    monkeypatch.setattr("src.config.settings.ollama_model", "qwen2.5:7b")

    email = Email(
        id="111",
        thread_id="t111",
        subject="Invoice #456",
        sender="billing@cloud.com",
        body="Here is your invoice for this month.",
        received_at=datetime.now(UTC),
    )

    mock_response_data = {"message": {"content": '{"confirmed": true}'}}

    class MockResponse:
        def __init__(self, json_data):
            self.json_data = json_data

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass

    client = httpx.Client()
    monkeypatch.setattr(
        client, "post", lambda url, json, **kwargs: MockResponse(mock_response_data)
    )

    adapter = GenericLLMAdapter(client=client)
    res = adapter.check_commercial_pattern([email])

    assert res is True


def test_generic_llm_adapter_generic_openai_provider(monkeypatch):
    monkeypatch.setattr("src.config.settings.llm_provider", "openai_compatible")
    monkeypatch.setattr("src.config.settings.llm_base_url", "https://api.openai.com/v1")
    monkeypatch.setattr("src.config.settings.llm_api_key", "sk-testkey")
    monkeypatch.setattr("src.config.settings.ollama_model", "gpt-4o")

    email = Email(
        id="111",
        thread_id="t111",
        subject="Newsletter",
        sender="news@letter.com",
        body="Read our weekly articles.",
        received_at=datetime.now(UTC),
    )

    mock_response_data = {
        "choices": [{"message": {"content": '{"is_newsletter": true}'}}]
    }

    class MockResponse:
        def __init__(self, json_data):
            self.json_data = json_data

        def json(self):
            return self.json_data

        def raise_for_status(self):
            pass

    def mock_post(url, headers, json, **kwargs):
        assert "https://api.openai.com/v1/chat/completions" in url
        assert headers["Authorization"] == "Bearer sk-testkey"
        assert json["response_format"]["type"] == "json_object"
        return MockResponse(mock_response_data)

    client = httpx.Client()
    monkeypatch.setattr(client, "post", mock_post)

    adapter = GenericLLMAdapter(client=client)
    res = adapter.is_newsletter_sender([email])

    assert res is True
