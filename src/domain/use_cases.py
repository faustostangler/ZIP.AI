from src.domain.entities import ClassificationResult
from src.ports.gmail import GmailPort
from src.ports.llm import LLMPort

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
                email_id=email.id,
                action=result.action,
                label_name=result.label_to_add
            )
            
        return results
