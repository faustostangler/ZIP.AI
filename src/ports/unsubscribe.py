from abc import ABC, abstractmethod


class UnsubscribePort(ABC):
    """
    Port (interface) defining operations to perform automatic unsubscriptions.
    """

    @abstractmethod
    def unsubscribe(self, url: str) -> bool:
        """
        Send a GET request to the unsubscribe URL to attempt automated unsubscription.

        Args:
            url: The unsubscribe target link.

        Returns:
            True if request succeeded, False otherwise.
        """
        pass
