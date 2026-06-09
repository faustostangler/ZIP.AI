from datetime import datetime, timezone
from unittest.mock import MagicMock
import pytest
from src.domain.entities import Email, EmailAction, ClassificationResult
from src.ports.gmail import GmailPort
from src.ports.llm import LLMPort

# Since the use case doesn't exist yet, this import will fail, making our test environment RED.
# Once we write the implementation, it will turn GREEN.
from src.domain.use_cases import ProcessInboxUseCase


def test_process_inbox_success():
    """
    Test that ProcessInboxUseCase fetches emails, classifies them, and applies the action.
    """
    # 1. Arrange
    mock_gmail = MagicMock(spec=GmailPort)
    mock_llm = MagicMock(spec=LLMPort)
    
    test_email = Email(
        id="msg-123",
        thread_id="thread-123",
        subject="Congratulations! You won a million dollars!",
        sender="spammer@spam.com",
        body="Click here to claim your money",
        received_at=datetime.now(timezone.utc),
        labels=["UNREAD"]
    )
    
    test_classification = ClassificationResult(
        email_id="msg-123",
        action=EmailAction.DELETE,
        label_to_add=None,
        reason="Looks like phishing/spam"
    )
    
    mock_gmail.fetch_unread_emails.return_value = [test_email]
    mock_llm.classify_email.return_value = test_classification
    
    use_case = ProcessInboxUseCase(gmail_port=mock_gmail, llm_port=mock_llm)
    
    # 2. Act
    results = use_case.execute(max_emails=10)
    
    # 3. Assert
    mock_gmail.fetch_unread_emails.assert_called_once_with(max_results=10)
    mock_llm.classify_email.assert_called_once_with(test_email)
    mock_gmail.apply_action.assert_called_once_with(
        email_id="msg-123",
        action=EmailAction.DELETE,
        label_name=None
    )
    
    assert len(results) == 1
    assert results[0] == test_classification


def test_process_inbox_no_emails():
    """
    Test that if no unread emails are found, the classifier is not called.
    """
    mock_gmail = MagicMock(spec=GmailPort)
    mock_llm = MagicMock(spec=LLMPort)
    
    mock_gmail.fetch_unread_emails.return_value = []
    
    use_case = ProcessInboxUseCase(gmail_port=mock_gmail, llm_port=mock_llm)
    results = use_case.execute()
    
    mock_gmail.fetch_unread_emails.assert_called_once()
    mock_llm.classify_email.assert_not_called()
    mock_gmail.apply_action.assert_not_called()
    assert len(results) == 0
