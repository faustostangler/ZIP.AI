import re
from email.utils import parseaddr

from src.domain.entities import ClassificationResult
from src.ports.gmail import GmailPort
from src.ports.llm import LLMPort
from src.ports.processed_senders import ProcessedSendersPort
from src.ports.unsubscribe import UnsubscribePort


class ProcessInboxUseCase:
    """
    Use case responsible for orchestrating Gmail inbox cleaning and categorization.
    """

    def __init__(self, gmail_port: GmailPort, llm_port: LLMPort) -> None:
        self.gmail_port = gmail_port
        self.llm_port = llm_port

    def execute(self, max_emails: int = 20) -> list[ClassificationResult]:
        """
        Coordinates the workflow:
        1. Fetch unread emails.
        2. Send each email to the LLM for classification.
        3. Apply the recommended actions in Gmail.
        4. Automate filter creation for highly confident commercial/spam senders.

        Args:
            max_emails: Maximum number of unread emails to process.

        Returns:
            A list of ClassificationResult entities.
        """
        emails = self.gmail_port.fetch_unread_emails(max_results=max_emails)
        results: list[ClassificationResult] = []

        for email in emails:
            # Let the LLM decide what to do with the email
            result = self.llm_port.classify_email(email)
            results.append(result)

            # Perform action (archive, delete, label) in Gmail API
            self.gmail_port.apply_action(
                email_id=email.id, action=result.action, label_name=result.label_to_add
            )

            # Check if commercial/spam filter automation should be triggered
            if result.is_commercial and result.confidence >= 0.8:
                _, sender_email = parseaddr(email.sender)
                if sender_email and not self.gmail_port.filter_exists(sender_email):
                    past_emails = self.gmail_port.fetch_emails_by_sender(
                        sender_email, max_results=5
                    )
                    if self.llm_port.check_commercial_pattern(past_emails):
                        self.gmail_port.create_commercial_filter(sender_email)

        return results


class ProcessSenderCentricFiltersUseCase:
    """
    Use case responsible for identifying unprocessed senders in the Gmail inbox,
    analyzing their email history, and creating automatic filters.
    """

    def __init__(
        self,
        gmail_port: GmailPort,
        llm_port: LLMPort,
        processed_senders_port: ProcessedSendersPort,
        unsubscribe_port: UnsubscribePort,
    ) -> None:
        self.gmail_port = gmail_port
        self.llm_port = llm_port
        self.processed_senders_port = processed_senders_port
        self.unsubscribe_port = unsubscribe_port

    def _find_unsubscribe_link(self, body: str) -> str | None:
        # Find all URLs in the body
        urls = re.findall(r'https?://[^\s<>"]+', body)

        # First pass: check if any URL itself contains unsubscribe-like keywords
        unsub_url_keywords = [
            "unsubscribe",
            "unsub",
            "optout",
            "opt-out",
            "descadastrar",
            "desinscrever",
            "cancelar",
        ]
        for url in urls:
            url_lower = url.lower()
            if any(kw in url_lower for kw in unsub_url_keywords):
                return url

        # Second pass: check if body contains unsubscribe keywords, and if so, check if we have any URL
        body_lower = body.lower()
        body_keywords = [
            "unsubscribe",
            "opt out",
            "opt-out",
            "desinscrever",
            "descadastrar",
            "cancelar inscrição",
            "cancelar inscricao",
        ]
        if any(kw in body_lower for kw in body_keywords) and urls:
            # Return the last URL, as unsubscribe links are usually at the bottom of the email
            return urls[-1]

        return None

    def execute(self) -> str | None:
        """
        Coordinates the workflow:
        1. Fetch unread or recent messages in the inbox.
        2. Identify the first sender that has not yet been processed locally.
        3. Retrieve history (all past messages) from that sender.
        4. Check for unsubscribe links in email bodies. If found, request link and bypass LLM.
        5. Otherwise, classify sender via AI (Newsletter vs Transactional).
        6. If newsletter, create filter in Gmail to route messages directly to trash.
        7. Persist sender state as processed.

        Returns:
            The processed sender email address, or None if no unseen sender was found.
        """
        # Fetch unread emails to inspect latest senders
        emails = self.gmail_port.fetch_unread_emails(max_results=50)
        target_sender = None

        for email in emails:
            _, sender_email = parseaddr(email.sender)
            if not sender_email:
                continue
            sender_email = sender_email.strip().lower()
            if not self.processed_senders_port.is_processed(sender_email):
                target_sender = sender_email
                break

        if not target_sender:
            return None

        # Fetch history for this sender
        history = self.gmail_port.fetch_emails_by_sender(target_sender, max_results=10)

        # Scan history for unsubscribe links
        unsub_link = None
        for email in history:
            link = self._find_unsubscribe_link(email.body)
            if link:
                unsub_link = link
                break

        is_newsletter = False
        if unsub_link:
            # Attempt to request unsubscribe link, bypassing LLM
            self.unsubscribe_port.unsubscribe(unsub_link)
            is_newsletter = True
        else:
            is_newsletter = self.llm_port.is_newsletter_sender(history)

        if is_newsletter:
            self.gmail_port.create_commercial_filter(target_sender)

        # Mark sender as processed in local storage
        self.processed_senders_port.mark_as_processed(target_sender)

        return target_sender
