from abc import ABC, abstractmethod
from src.domain.entities import Email, EmailAction

class GmailPort(ABC):
    """
    Port (interface) defining the outgoing operations to interact with Gmail.
    """

    @abstractmethod
    def fetch_unread_emails(self, max_results: int = 20) -> list[Email]:
        """
        Fetches unread emails from the user's inbox.

        Args:
            max_results: Maximum number of unread emails to retrieve.

        Returns:
            A list of Email domain entities.
        """
        pass

    @abstractmethod
    def apply_action(
        self, email_id: str, action: EmailAction, label_name: str | None = None
    ) -> None:
        """
        Applies a classification action to a specific email.

        Args:
            email_id: The unique identifier of the email.
            action: The EmailAction to apply (e.g. DELETE, ARCHIVE, LABEL).
            label_name: Optional name of the label to apply (used if action is LABEL).
        """
        pass
