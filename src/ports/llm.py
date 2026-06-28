from abc import ABC, abstractmethod

from src.domain.entities import ClassificationResult, Email


class LLMPort(ABC):
    """
    Port (interface) defining the outgoing operations to classify emails using LLMs.
    """

    @abstractmethod
    def classify_email(self, email: Email) -> ClassificationResult:
        """
        Submits an email to the LLM for classification.

        Args:
            email: The Email entity to analyze.

        Returns:
            A ClassificationResult entity containing the action and reasoning.
        """
        pass

    @abstractmethod
    def check_commercial_pattern(self, emails: list[Email]) -> bool:
        """
        Submits list of emails to the LLM to verify if they match a commercial pattern.
        """
        pass

    @abstractmethod
    def is_newsletter_sender(self, emails: list[Email]) -> bool:
        """
        Analyzes a list of historical emails from a single sender to determine
        if they represent a newsletter pattern (True) or a transactional/personal one (False).
        """
        pass
