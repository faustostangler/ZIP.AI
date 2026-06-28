import json
import logging

import httpx

from src.config import settings
from src.domain.entities import ClassificationResult, Email, EmailAction
from src.ports.llm import LLMPort

logger = logging.getLogger("zip.generic_llm")


class GenericLLMAdapter(LLMPort):
    """
    Adapter implementing LLMPort that can call either Ollama or an external generic LLM endpoint.
    """

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(timeout=30.0)
        self.provider = settings.llm_provider.lower()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model
        self.api_key = settings.llm_api_key

    def _call_ollama(self, messages: list[dict], schema: dict) -> str:
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "format": schema,
            "stream": False,
            "options": {
                "temperature": 0.0,
            },
        }
        response = self.client.post(url, json=payload)
        response.raise_for_status()
        return str(response.json()["message"]["content"])

    def _call_generic(self, messages: list[dict], schema: dict) -> str:
        # Generic OpenAI-compatible chat completion endpoint
        url = f"{settings.llm_base_url or self.base_url}/chat/completions"
        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": messages,
            "response_format": {
                "type": "json_object",
                "schema": schema,
            },
            "temperature": 0.0,
        }
        response = self.client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return str(response.json()["choices"][0]["message"]["content"])

    def classify_email(self, email: Email) -> ClassificationResult:
        system_prompt = (
            "You are a Zero Inbox Assistant. Analyze the incoming email and decide the appropriate action.\n"
            "Actions:\n"
            " - 'archive': Notifications, receipts, newsletters, updates that do not require reply.\n"
            " - 'delete': SPAM, phishing, malicious, unsolicited commercial advertisements, junk.\n"
            " - 'label': Work, personal, shopping, financial, or travel emails that need classification label.\n"
            " - 'none': Important emails that require direct user attention and should stay in the inbox.\n\n"
            "Identify if it is a commercial newsletter, promotion, advertisement, or spam/junk in 'is_commercial' (boolean).\n"
            "Provide a confidence score between 0.0 and 1.0 in 'confidence' (number).\n"
            "You must return a JSON object that matches the requested schema precisely."
        )

        user_prompt = (
            f"Email ID: {email.id}\n"
            f"Sender: {email.sender}\n"
            f"Subject: {email.subject}\n"
            f"Received: {email.received_at.isoformat()}\n"
            f"Body:\n{email.body[:1500]}"
        )

        schema = {
            "type": "object",
            "properties": {
                "email_id": {"type": "string"},
                "action": {
                    "type": "string",
                    "enum": ["archive", "delete", "label", "none"],
                },
                "label_to_add": {"type": ["string", "null"]},
                "reason": {"type": "string"},
                "is_commercial": {"type": "boolean"},
                "confidence": {"type": "number"},
            },
            "required": [
                "email_id",
                "action",
                "label_to_add",
                "reason",
                "is_commercial",
                "confidence",
            ],
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            if self.provider == "ollama":
                content = self._call_ollama(messages, schema)
            else:
                content = self._call_generic(messages, schema)

            result_json = ClassificationResult.model_validate_json(content)
            result_json.email_id = email.id
            return result_json
        except Exception as e:
            logger.error(f"Failed classification for {email.id}: {e}", exc_info=True)
            return ClassificationResult(
                email_id=email.id,
                action=EmailAction.NONE,
                label_to_add=None,
                reason=f"Failed classification: {e!s}",
                is_commercial=False,
                confidence=1.0,
            )

    def check_commercial_pattern(self, emails: list[Email]) -> bool:
        if not emails:
            return False

        system_prompt = (
            "You are an email pattern analysis assistant. Analyze the list of emails from a single sender "
            "and determine if they represent a commercial pattern (newsletters, promotions, automatic alerts, spam, junk).\n"
            "Return JSON matching the schema precisely."
        )

        email_summaries = []
        for idx, email in enumerate(emails, start=1):
            email_summaries.append(
                f"Email {idx}:\nSubject: {email.subject}\nSnippet: {email.body[:300]}"
            )

        user_prompt = "Emails from sender:\n\n" + "\n\n".join(email_summaries)

        schema = {
            "type": "object",
            "properties": {"confirmed": {"type": "boolean"}},
            "required": ["confirmed"],
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            if self.provider == "ollama":
                content = self._call_ollama(messages, schema)
            else:
                content = self._call_generic(messages, schema)

            result = json.loads(content)
            return bool(result.get("confirmed", False))
        except Exception as e:
            logger.error(f"Failed check_commercial_pattern: {e}", exc_info=True)
            return False

    def is_newsletter_sender(self, emails: list[Email]) -> bool:
        if not emails:
            return False

        system_prompt = (
            "You are an email analysis bot. Analyze the sender's history and decide if the sender is a Newsletter "
            "(automatic promotions, newsletters, updates, subscriptions) or Transactional/Personal (specific receipts, "
            "personal replies, critical single updates, passwords).\n"
            "Return JSON matching the schema precisely."
        )

        email_summaries = []
        for idx, email in enumerate(emails, start=1):
            email_summaries.append(
                f"Email {idx}:\nSubject: {email.subject}\nSnippet: {email.body[:300]}"
            )

        user_prompt = "Emails from sender:\n\n" + "\n\n".join(email_summaries)

        schema = {
            "type": "object",
            "properties": {"is_newsletter": {"type": "boolean"}},
            "required": ["is_newsletter"],
        }

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            if self.provider == "ollama":
                content = self._call_ollama(messages, schema)
            else:
                content = self._call_generic(messages, schema)

            result = json.loads(content)
            return bool(result.get("is_newsletter", False))
        except Exception as e:
            logger.error(f"Failed is_newsletter_sender check: {e}", exc_info=True)
            return False
