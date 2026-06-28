from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest

from src.domain.entities import Email
from src.domain.use_cases import ProcessSenderCentricFiltersUseCase
from src.ports.gmail import GmailPort
from src.ports.llm import LLMPort
from src.ports.processed_senders import ProcessedSendersPort
from src.ports.unsubscribe import UnsubscribePort


@pytest.fixture
def mock_gmail_port():
    return MagicMock(spec=GmailPort)


@pytest.fixture
def mock_llm_port():
    return MagicMock(spec=LLMPort)


@pytest.fixture
def mock_processed_senders_port():
    return MagicMock(spec=ProcessedSendersPort)


@pytest.fixture
def mock_unsubscribe_port():
    return MagicMock(spec=UnsubscribePort)


def test_use_case_newsletter_happy_path(
    mock_gmail_port, mock_llm_port, mock_processed_senders_port, mock_unsubscribe_port
):
    # Setup mocks
    email = Email(
        id="123",
        thread_id="thread_123",
        subject="Daily Deal",
        sender="Promotions <promo@store.com>",
        body="Check out our daily deals!",
        received_at=datetime.now(UTC),
    )
    mock_gmail_port.fetch_unread_emails.return_value = [email]

    # promo@store.com is not processed yet
    mock_processed_senders_port.is_processed.return_value = False

    # Mock history fetching
    history_emails = [email]
    mock_gmail_port.fetch_emails_by_sender.return_value = history_emails

    # LLM classifies as newsletter
    mock_llm_port.is_newsletter_sender.return_value = True

    use_case = ProcessSenderCentricFiltersUseCase(
        gmail_port=mock_gmail_port,
        llm_port=mock_llm_port,
        processed_senders_port=mock_processed_senders_port,
        unsubscribe_port=mock_unsubscribe_port,
    )

    result = use_case.execute()

    assert result == "promo@store.com"
    mock_processed_senders_port.is_processed.assert_called_once_with("promo@store.com")
    mock_gmail_port.fetch_emails_by_sender.assert_called_once_with(
        "promo@store.com", max_results=10
    )
    mock_llm_port.is_newsletter_sender.assert_called_once_with(history_emails)
    mock_gmail_port.create_commercial_filter.assert_called_once_with("promo@store.com")
    mock_processed_senders_port.mark_as_processed.assert_called_once_with(
        "promo@store.com"
    )
    mock_unsubscribe_port.unsubscribe.assert_not_called()


def test_use_case_transactional_no_filter(
    mock_gmail_port, mock_llm_port, mock_processed_senders_port, mock_unsubscribe_port
):
    email = Email(
        id="456",
        thread_id="thread_456",
        subject="Your Invoice",
        sender="Billing <billing@cloud.com>",
        body="Here is your invoice.",
        received_at=datetime.now(UTC),
    )
    mock_gmail_port.fetch_unread_emails.return_value = [email]
    mock_processed_senders_port.is_processed.return_value = False
    mock_gmail_port.fetch_emails_by_sender.return_value = [email]

    # LLM classifies as transactional (not newsletter)
    mock_llm_port.is_newsletter_sender.return_value = False

    use_case = ProcessSenderCentricFiltersUseCase(
        gmail_port=mock_gmail_port,
        llm_port=mock_llm_port,
        processed_senders_port=mock_processed_senders_port,
        unsubscribe_port=mock_unsubscribe_port,
    )

    result = use_case.execute()

    assert result == "billing@cloud.com"
    # No filter should be created
    mock_gmail_port.create_commercial_filter.assert_not_called()
    # But it must be marked as processed so we don't re-evaluate
    mock_processed_senders_port.mark_as_processed.assert_called_once_with(
        "billing@cloud.com"
    )
    mock_unsubscribe_port.unsubscribe.assert_not_called()


def test_use_case_skip_already_processed(
    mock_gmail_port, mock_llm_port, mock_processed_senders_port, mock_unsubscribe_port
):
    email_processed = Email(
        id="111",
        thread_id="t111",
        subject="Processed Email",
        sender="already@processed.com",
        body="hi",
        received_at=datetime.now(UTC),
    )
    email_new = Email(
        id="222",
        thread_id="t222",
        subject="New Email",
        sender="new@sender.com",
        body="hello",
        received_at=datetime.now(UTC),
    )
    mock_gmail_port.fetch_unread_emails.return_value = [email_processed, email_new]

    # already@processed.com is processed; new@sender.com is not
    mock_processed_senders_port.is_processed.side_effect = lambda email: (
        email == "already@processed.com"
    )
    mock_gmail_port.fetch_emails_by_sender.return_value = [email_new]
    mock_llm_port.is_newsletter_sender.return_value = False

    use_case = ProcessSenderCentricFiltersUseCase(
        gmail_port=mock_gmail_port,
        llm_port=mock_llm_port,
        processed_senders_port=mock_processed_senders_port,
        unsubscribe_port=mock_unsubscribe_port,
    )

    result = use_case.execute()

    assert result == "new@sender.com"
    mock_processed_senders_port.mark_as_processed.assert_called_once_with(
        "new@sender.com"
    )
    mock_unsubscribe_port.unsubscribe.assert_not_called()


def test_use_case_all_senders_processed(
    mock_gmail_port, mock_llm_port, mock_processed_senders_port, mock_unsubscribe_port
):
    email = Email(
        id="999",
        thread_id="t999",
        subject="Hello",
        sender="already@processed.com",
        body="hi",
        received_at=datetime.now(UTC),
    )
    mock_gmail_port.fetch_unread_emails.return_value = [email]
    mock_processed_senders_port.is_processed.return_value = True

    use_case = ProcessSenderCentricFiltersUseCase(
        gmail_port=mock_gmail_port,
        llm_port=mock_llm_port,
        processed_senders_port=mock_processed_senders_port,
        unsubscribe_port=mock_unsubscribe_port,
    )

    result = use_case.execute()

    assert result is None
    mock_gmail_port.fetch_emails_by_sender.assert_not_called()
    mock_llm_port.is_newsletter_sender.assert_not_called()
    mock_unsubscribe_port.unsubscribe.assert_not_called()


def test_use_case_bypass_via_unsubscribe_link(
    mock_gmail_port, mock_llm_port, mock_processed_senders_port, mock_unsubscribe_port
):
    email = Email(
        id="123",
        thread_id="thread_123",
        subject="Weekly Ads",
        sender="Promotions <promo@store.com>",
        # Body contains unsubscribe keywords and a URL
        body="Please unsubscribe at https://newsletter.com/unsub",
        received_at=datetime.now(UTC),
    )
    mock_gmail_port.fetch_unread_emails.return_value = [email]
    mock_processed_senders_port.is_processed.return_value = False
    mock_gmail_port.fetch_emails_by_sender.return_value = [email]

    use_case = ProcessSenderCentricFiltersUseCase(
        gmail_port=mock_gmail_port,
        llm_port=mock_llm_port,
        processed_senders_port=mock_processed_senders_port,
        unsubscribe_port=mock_unsubscribe_port,
    )

    result = use_case.execute()

    assert result == "promo@store.com"
    # LLM should be bypassed
    mock_llm_port.is_newsletter_sender.assert_not_called()
    # Unsubscribe link should be called
    mock_unsubscribe_port.unsubscribe.assert_called_once_with(
        "https://newsletter.com/unsub"
    )
    # Filter should be created
    mock_gmail_port.create_commercial_filter.assert_called_once_with("promo@store.com")
    # Sender should be marked processed
    mock_processed_senders_port.mark_as_processed.assert_called_once_with(
        "promo@store.com"
    )
