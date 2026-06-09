from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field

class EmailAction(str, Enum):
    ARCHIVE = "archive"
    DELETE = "delete"
    LABEL = "label"
    NONE = "none"

class Email(BaseModel):
    """
    Domain entity representing an email retrieved from Gmail.
    """
    id: str = Field(..., description="Unique Gmail message ID")
    thread_id: str = Field(..., description="Gmail thread ID")
    subject: str = Field(default="", description="Email subject line")
    sender: str = Field(..., description="Sender name and email address")
    body: str = Field(default="", description="Snippet or full body of the email text")
    received_at: datetime = Field(..., description="Timestamp of when the email was received")
    labels: list[str] = Field(default_factory=list, description="Currently applied Gmail labels")

class ClassificationResult(BaseModel):
    """
    Domain entity representing the LLM classification decision for an email.
    """
    email_id: str = Field(..., description="Associated Gmail message ID")
    action: EmailAction = Field(
        default=EmailAction.NONE,
        description="Recommended action to take: archive, delete, label, or none"
    )
    label_to_add: str | None = Field(
        default=None,
        description="Target label name if action is 'label'"
    )
    reason: str = Field(
        default="",
        description="Reasoning explaining the classification choice"
    )
