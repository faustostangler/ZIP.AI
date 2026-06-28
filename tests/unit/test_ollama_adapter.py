import json
from datetime import UTC, datetime
from unittest.mock import MagicMock

import httpx

from src.adapters.ollama_adapter import OllamaLLMAdapter
from src.config import settings
from src.domain.entities import Email, EmailAction


def test_ollama_classify_success():
    mock_client = MagicMock(spec=httpx.Client)

    mock_response_data = {
        "message": {
            "content": json.dumps(
                {
                    "email_id": "msg-123",
                    "action": "delete",
                    "label_to_add": None,
                    "reason": "Phishing detection",
                    "is_commercial": True,
                    "confidence": 0.95,
                }
            )
        }
    }

    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_client.post.return_value = mock_response

    adapter = OllamaLLMAdapter(client=mock_client)

    test_email = Email(
        id="msg-123",
        thread_id="thread-123",
        subject="Get rich quick!",
        sender="scam@scam.com",
        body="Send us money now",
        received_at=datetime.now(UTC),
        labels=[],
    )

    result = adapter.classify_email(test_email)

    assert result.email_id == "msg-123"
    assert result.action == EmailAction.DELETE
    assert result.label_to_add is None
    assert result.reason == "Phishing detection"
    assert result.is_commercial is True
    assert result.confidence == 0.95

    mock_client.post.assert_called_once()
    call_args, call_kwargs = mock_client.post.call_args
    assert call_args[0].endswith("/api/chat")
    payload = call_kwargs["json"]
    assert payload["model"] == settings.ollama_model
    assert len(payload["messages"]) == 2
    assert payload["format"]["type"] == "object"


def test_ollama_classify_http_error():
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.HTTPError("Connection refused")

    adapter = OllamaLLMAdapter(client=mock_client)

    test_email = Email(
        id="msg-456",
        thread_id="thread-456",
        subject="Hello",
        sender="friend@friend.com",
        body="Hey there!",
        received_at=datetime.now(UTC),
        labels=[],
    )

    result = adapter.classify_email(test_email)

    assert result.email_id == "msg-456"
    assert result.action == EmailAction.NONE
    assert result.label_to_add is None
    assert "Failed classification due to Ollama error" in result.reason
    assert result.is_commercial is False
    assert result.confidence == 1.0


def test_ollama_check_commercial_pattern_success():
    mock_client = MagicMock(spec=httpx.Client)
    mock_response_data = {"message": {"content": json.dumps({"confirmed": True})}}
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = mock_response_data
    mock_client.post.return_value = mock_response

    adapter = OllamaLLMAdapter(client=mock_client)
    test_email = Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Promo",
        sender="shop@store.com",
        body="Buy now",
        received_at=datetime.now(UTC),
        labels=[],
    )

    confirmed = adapter.check_commercial_pattern([test_email])
    assert confirmed is True
    mock_client.post.assert_called_once()


def test_ollama_check_commercial_pattern_error():
    mock_client = MagicMock(spec=httpx.Client)
    mock_client.post.side_effect = httpx.HTTPError("Connection refused")

    adapter = OllamaLLMAdapter(client=mock_client)
    test_email = Email(
        id="msg-1",
        thread_id="thread-1",
        subject="Promo",
        sender="shop@store.com",
        body="Buy now",
        received_at=datetime.now(UTC),
        labels=[],
    )

    confirmed = adapter.check_commercial_pattern([test_email])
    assert confirmed is False
