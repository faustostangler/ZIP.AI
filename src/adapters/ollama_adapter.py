import logging
import httpx
from src.config import settings
from src.domain.entities import Email, ClassificationResult, EmailAction
from src.ports.llm import LLMPort

logger = logging.getLogger("zip.ollama")

class OllamaLLMAdapter(LLMPort):
    """
    Adapter implementation for LLMPort that communicates with a local Ollama instance.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30.0)
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    def classify_email(self, email: Email) -> ClassificationResult:
        """
        Sends the email to the local Ollama model for classification.
        Enforces structured JSON output.
        """
        system_prompt = (
            "You are a Zero Inbox Assistant. Analyze the incoming email and decide the appropriate action.\n"
            "Actions:\n"
            " - 'archive': Notifications, receipts, newsletters, updates that do not require reply.\n"
            " - 'delete': SPAM, phishing, malicious, unsolicited commercial advertisements, junk.\n"
            " - 'label': Work, personal, shopping, financial, or travel emails that need classification label.\n"
            " - 'none': Important emails that require direct user attention and should stay in the inbox.\n\n"
            "You must return a JSON object that matches the requested schema precisely."
        )

        user_prompt = (
            f"Email ID: {email.id}\n"
            f"Sender: {email.sender}\n"
            f"Subject: {email.subject}\n"
            f"Received: {email.received_at.isoformat()}\n"
            f"Body:\n{email.body[:1500]}"  # Truncate body to fit context window comfortably
        )

        # JSON schema for Ollama structured generation
        schema = {
            "type": "object",
            "properties": {
                "email_id": {"type": "string"},
                "action": {"type": "string", "enum": ["archive", "delete", "label", "none"]},
                "label_to_add": {"type": ["string", "null"]},
                "reason": {"type": "string"}
            },
            "required": ["email_id", "action", "label_to_add", "reason"]
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": schema,
            "stream": False,
            "options": {
                "temperature": 0.0  # Determinstic output
            }
        }

        url = f"{self.base_url}/api/chat"

        try:
            logger.info(f"Classifying email {email.id} using Ollama model '{self.model}'")
            response = self.client.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            message_content = data["message"]["content"]
            logger.debug(f"Ollama raw response for {email.id}: {message_content}")
            
            # Load the JSON result
            result_json = ClassificationResult.model_validate_json(message_content)
            
            # Ensure the email_id matches
            result_json.email_id = email.id
            return result_json

        except Exception as e:
            logger.error(f"Failed to classify email {email.id} via Ollama: {e}", exc_info=True)
            # Fail-safe fallback: keep in inbox (none) with error context
            return ClassificationResult(
                email_id=email.id,
                action=EmailAction.NONE,
                label_to_add=None,
                reason=f"Failed classification due to Ollama error: {str(e)}"
            )
