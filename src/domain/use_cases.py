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
        body_lower = body.lower()

        # 1. Keywords to search for
        keywords = [
            "unsubscribe",
            "opt-out",
            "opt out",
            "descadastrar",
            "desinscrever",
            "cancelar inscrição",
            "cancelar inscricao",
            "cancelar assinatura",
            "sair da lista",
        ]

        # Check if any keyword is in the body
        if not any(kw in body_lower for kw in keywords):
            return None

        # 2. Try to find a URL that contains unsubscribe keywords inside the URL itself
        urls = re.findall(r'https?://[^\s<>"]+', body)
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

        # 3. Look for a URL that is close to the keyword in the text (proximity match within 150 chars)
        for kw in keywords:
            # Match keyword followed by text, then URL
            pattern_after = re.compile(
                rf"{re.escape(kw)}[\s\S]{{0,150}}?(https?://[^\s<>\"\u200b]+)",
                re.IGNORECASE,
            )
            match = pattern_after.search(body)
            if match:
                return match.group(1).rstrip(".,;)]}>")

            # Match URL followed by text, then keyword
            pattern_before = re.compile(
                rf"(https?://[^\s<>\"\u200b]+)[\s\S]{{0,150}}?{re.escape(kw)}",
                re.IGNORECASE,
            )
            match = pattern_before.search(body)
            if match:
                return match.group(1).rstrip(".,;)]}>")

        # 4. Fallback: if keywords exist in the body, but no direct proximity match, return the last URL
        if urls:
            return urls[-1]

        return None

    def execute(self) -> list[str]:
        """
        Coordinates the workflow:
        1. Fetch unread messages in the inbox.
        2. Identify unprocessed senders message-by-message.
        3. For each unseen sender, retrieve history and process them.
        4. If unsubscribe link found, request it and bypass LLM. Otherwise, classify via LLM.
        5. If newsletter, create filter in Gmail to route messages directly to trash.
        6. Persist sender state as processed.

        Returns:
            The list of processed sender email addresses.
        """
        # Fetch unread emails to inspect latest senders
        emails = self.gmail_port.fetch_unread_emails(max_results=100)
        processed_senders = []
        processed_set = set()

        for email in emails:
            _, sender_email = parseaddr(email.sender)
            if not sender_email:
                continue
            sender_email = sender_email.strip().lower()

            # Skip if already processed in this batch or globally
            if (
                sender_email in processed_set
                or self.processed_senders_port.is_processed(sender_email)
            ):
                continue

            # Fetch history for this sender
            history = self.gmail_port.fetch_emails_by_sender(
                sender_email, max_results=10
            )

            # Scan history for unsubscribe links
            unsub_link = None
            for hist_email in history:
                link = self._find_unsubscribe_link(hist_email.body)
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
                self.gmail_port.create_commercial_filter(sender_email)

            # Mark sender as processed in local storage and memory
            self.processed_senders_port.mark_as_processed(sender_email)
            processed_set.add(sender_email)
            processed_senders.append(sender_email)

        return processed_senders
