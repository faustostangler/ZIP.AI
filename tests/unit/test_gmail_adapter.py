from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from googleapiclient.errors import HttpError

from src.adapters.gmail_adapter import GmailOAuthAdapter
from src.domain.entities import EmailAction


# Mock out _get_credentials and build to avoid real Auth/API calls in __init__
@pytest.fixture
def mock_gmail_adapter():
    with (
        patch(
            "src.adapters.gmail_adapter.GmailOAuthAdapter._get_credentials"
        ) as mock_get_creds,
        patch("src.adapters.gmail_adapter.build") as mock_build,
    ):
        mock_get_creds.return_value = MagicMock()
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        adapter = GmailOAuthAdapter()
        yield adapter, mock_service


def test_fetch_unread_emails_success(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter

    # Mock list messages API
    mock_list_exec = mock_service.users().messages().list().execute
    mock_list_exec.return_value = {
        "messages": [{"id": "msg-1", "threadId": "thread-1"}]
    }

    # Mock get message API
    mock_get_exec = mock_service.users().messages().get().execute
    mock_get_exec.return_value = {
        "id": "msg-1",
        "threadId": "thread-1",
        "labelIds": ["UNREAD", "INBOX"],
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Test Subject"},
                {"name": "From", "value": "sender@test.com"},
                {"name": "Date", "value": "Tue, 09 Jun 2026 15:00:00 -0300"},
            ],
            "body": {
                # base64url encoded "Hello World"
                "data": "SGVsbG8gV29ybGQ="
            },
        },
    }

    emails = adapter.fetch_unread_emails(max_results=5)

    assert len(emails) == 1
    email = emails[0]
    assert email.id == "msg-1"
    assert email.thread_id == "thread-1"
    assert email.subject == "Test Subject"
    assert email.sender == "sender@test.com"
    assert email.body == "Hello World"
    assert "UNREAD" in email.labels


def test_fetch_unread_emails_date_fallback(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter

    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg-1", "threadId": "thread-1"}]
    }

    mock_service.users().messages().get().execute.return_value = {
        "id": "msg-1",
        "threadId": "thread-1",
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": "Test"},
                {"name": "From", "value": "sender@test.com"},
                {"name": "Date", "value": "INVALID_DATE_FORMAT"},
            ],
        },
    }

    emails = adapter.fetch_unread_emails(max_results=1)
    assert len(emails) == 1
    assert isinstance(emails[0].received_at, datetime)


def test_fetch_unread_emails_http_error(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter

    # Simulate HttpError
    mock_resp = MagicMock()
    mock_resp.status = 403
    mock_resp.reason = "Forbidden"
    mock_service.users().messages().list().execute.side_effect = HttpError(
        resp=mock_resp, content=b"error"
    )

    emails = adapter.fetch_unread_emails(max_results=5)
    assert emails == []


def test_apply_action_delete(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter
    mock_trash = mock_service.users().messages().trash

    adapter.apply_action("msg-1", EmailAction.DELETE)
    mock_trash.assert_called_once_with(userId="me", id="msg-1")
    mock_trash().execute.assert_called_once()


def test_apply_action_archive(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter
    mock_modify = mock_service.users().messages().modify

    adapter.apply_action("msg-1", EmailAction.ARCHIVE)
    mock_modify.assert_called_once_with(
        userId="me", id="msg-1", body={"removeLabelIds": ["INBOX", "UNREAD"]}
    )
    mock_modify().execute.assert_called_once()


def test_apply_action_label_exists(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter
    mock_modify = mock_service.users().messages().modify
    mock_labels_list = mock_service.users().labels().list

    # Label matches case insensitively
    mock_labels_list().execute.return_value = {
        "labels": [{"name": "work", "id": "label-work-123"}]
    }

    adapter.apply_action("msg-1", EmailAction.LABEL, "Work")

    mock_modify.assert_called_once_with(
        userId="me",
        id="msg-1",
        body={"addLabelIds": ["label-work-123"], "removeLabelIds": ["INBOX", "UNREAD"]},
    )


def test_apply_action_label_creates(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter
    mock_modify = mock_service.users().messages().modify
    mock_labels_list = mock_service.users().labels().list
    mock_labels_create = mock_service.users().labels().create

    mock_labels_list.return_value.execute.return_value = {"labels": []}
    mock_labels_create.return_value.execute.return_value = {"id": "new-label-id"}

    adapter.apply_action("msg-1", EmailAction.LABEL, "Personal")

    mock_labels_create.assert_called_once_with(
        userId="me",
        body={
            "name": "Personal",
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    )
    mock_modify.assert_called_once_with(
        userId="me",
        id="msg-1",
        body={"addLabelIds": ["new-label-id"], "removeLabelIds": ["INBOX", "UNREAD"]},
    )


def test_apply_action_none(mock_gmail_adapter):
    adapter, mock_service = mock_gmail_adapter
    mock_modify = mock_service.users().messages().modify

    adapter.apply_action("msg-1", EmailAction.NONE)
    mock_modify.assert_called_once_with(
        userId="me", id="msg-1", body={"removeLabelIds": ["UNREAD"]}
    )
