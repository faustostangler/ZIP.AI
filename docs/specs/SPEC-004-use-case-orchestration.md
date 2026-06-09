# SPEC-004: Use Case Orchestration Test Specification

This document details the test scenarios and invariants for `ProcessInboxUseCase`.

## Acceptance Criteria

### 1. Inbox Processing Workflow (`execute`)
*   **SPEC-004.1**: Fetches unread emails from Gmail port by calling `fetch_unread_emails` with the configured `max_emails`.
*   **SPEC-004.2**: Iterates over each fetched email and:
    *   Submits it to `LLMPort`'s `classify_email` function.
    *   Applies the returned classification action using `GmailPort`'s `apply_action` with the correct arguments (`email_id`, `action`, and `label_name`).
*   **SPEC-004.3**: Returns a list of all `ClassificationResult` items.
*   **SPEC-004.4**: If the unread message list is empty:
    *   Does not call `LLMPort` or call `apply_action` on the Gmail port.
    *   Returns an empty list `[]`.

## Test Strategy

*   **Unit Tests**: Standard unit tests in `tests/unit/test_use_cases.py` utilizing unittest mocks for `GmailPort` and `LLMPort`.
*   **Mutation Testing / Coverage**: Ensure 100% statement and branch coverage of the `ProcessInboxUseCase` execution block.
