# Glossary - Zero Inbox Gmail Project (ZIP.AI)

This glossary defines the Ubiquitous Language terms used across the ZIP.AI bounded contexts.

## Domain Terms

### Email
*   **Definition**: Domain entity representing an email retrieved from Gmail.
*   **Attributes**: `id`, `thread_id`, `subject`, `sender`, `body`, `received_at`, `labels`.
*   **Context**: Inbox Processing.

### ClassificationResult
*   **Definition**: Domain entity representing the LLM classification decision for a specific email.
*   **Attributes**: `email_id`, `action`, `label_to_add`, `reason`.
*   **Context**: LLM Categorization.

### EmailAction
*   **Definition**: Value Object (Enum) representing the concrete action to execute on an email.
*   **Values**:
    *   `ARCHIVE`: Move email out of Inbox by removing `INBOX` and `UNREAD` labels.
    *   `DELETE`: Move email to Gmail trash.
    *   `LABEL`: Apply a specific tag and archive the email.
    *   `NONE`: Keep email in Inbox but remove `UNREAD` to prevent re-processing.
*   **Context**: Inbox Processing.

### GmailPort
*   **Definition**: Outbound port defining operations to fetch and modify email states on Google Gmail API.
*   **Context**: Infrastructure Boundary.

### LLMPort
*   **Definition**: Outbound port defining operations to analyze and classify email content using language models.
*   **Context**: Infrastructure Boundary.
