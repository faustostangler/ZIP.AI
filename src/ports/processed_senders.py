from abc import ABC, abstractmethod


class ProcessedSendersPort(ABC):
    """
    Port (interface) defining operations to retrieve, track, and save processed email senders.
    """

    @abstractmethod
    def is_processed(self, email_address: str) -> bool:
        """
        Check if the given sender email address has already been processed.

        Args:
            email_address: The sender's email address to verify.

        Returns:
            True if processed, False otherwise.
        """
        pass

    @abstractmethod
    def mark_as_processed(self, email_address: str) -> None:
        """
        Mark the given sender email address as processed and persist this state.

        Args:
            email_address: The sender's email address to record.
        """
        pass

    @abstractmethod
    def get_all_processed(self) -> list[str]:
        """
        Retrieve all recorded processed email senders.

        Returns:
            A list of email addresses.
        """
        pass
