# SPEC-005: Commercial/Spam Filter Automation Test Specification

This document details the test scenarios and invariants for the commercial filter automation.

## Acceptance Criteria

### 1. Schema Validation
*   **SPEC-005.1**: `ClassificationResult` supports `is_commercial` (defaults to `False`) and `confidence` (defaults to `1.0`).

### 2. Usecase Logic (`ProcessInboxUseCase.execute`)
*   **SPEC-005.2**: If an email is classified with `is_commercial=True` and `confidence >= 0.8`:
    *   Extracts the email address from `sender`.
    *   Calls `gmail_port.filter_exists(sender_email)`.
*   **SPEC-005.3**: If the filter exists, does not fetch emails or call create.
*   **SPEC-005.4**: If the filter does not exist:
    *   Calls `gmail_port.fetch_emails_by_sender(sender_email)`.
    *   Calls `llm_port.check_commercial_pattern(emails)`.
*   **SPEC-005.5**: If the pattern is confirmed (`True`):
    *   Calls `gmail_port.create_commercial_filter(sender_email)`.
*   **SPEC-005.6**: If the pattern is not confirmed (`False`):
    *   Does not call `gmail_port.create_commercial_filter(sender_email)`.

### 3. Gmail Adapter Operations
*   **SPEC-005.7**: `fetch_emails_by_sender(sender_email)` queries Gmail messages with `q="from:{sender_email}"`.
*   **SPEC-005.8**: `filter_exists(sender_email)` lists existing filters and checks if any has `criteria.from` matching `sender_email`.
*   **SPEC-005.9**: `create_commercial_filter(sender_email)` makes a POST request to create a filter with `criteria.from = sender_email`, removing `UNREAD` and `INBOX`, and adding `TRASH`.

### 4. LLM Pattern Verification
*   **SPEC-005.10**: `check_commercial_pattern(emails)` sends email headers/snippets to Ollama, asking if they are commercial/spam, and returns the parsed boolean.

## Test Strategy

*   **Unit Tests**: Verify the orchestration logic using mocked ports, and adapter behavior using mocked API endpoints.
