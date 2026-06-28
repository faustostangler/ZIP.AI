# SPEC-002: Gmail Adapter Test Specification

This document details the test scenarios and invariants for the `GmailOAuthAdapter`.

## Acceptance Criteria

### 1. Fetching Unread Emails (`fetch_unread_emails`)
*   **SPEC-002.1**: Queries Gmail API with `q="is:unread"` up to `max_results`.
*   **SPEC-002.2**: Parses email headers correctly:
    *   `From` header maps to `sender`.
    *   `Subject` header maps to `subject`.
    *   `Date` header parses RFC 2822 format into timezone-aware `datetime`. Fallback to current UTC time if parsing fails.
*   **SPEC-002.3**: Body extraction decodes base64url encoded payload:
    *   If payload is flat `text/plain`, decodes content.
    *   If payload is multipart, recursively parses parts to find and aggregate `text/plain` parts.
*   **SPEC-002.4**: API errors (`HttpError`, generic exceptions) are caught, logged, and return an empty list `[]` (graceful degradation).

### 2. Applying Actions (`apply_action`)
*   **SPEC-002.5**: `DELETE` action calls `service.users().messages().trash` for target `email_id`.
*   **SPEC-002.6**: `ARCHIVE` action removes `INBOX` and `UNREAD` labels using `modify`.
*   **SPEC-002.7**: `LABEL` action:
    *   Queries user labels to match target label case-insensitively.
    *   Creates label if not found.
    *   Applies new label ID and removes `INBOX` and `UNREAD` labels.
*   **SPEC-002.8**: `NONE` action removes `UNREAD` label but keeps email in inbox.
*   **SPEC-002.9**: Errors during execution do not crash the runner; they are logged.

## Test Strategy

*   **Unit Tests**: Test logic in `fetch_unread_emails` and `apply_action` by mocking the discovery build `service` resource client.
*   **Integration Tests**: Run with dummy settings or environment check to skip real network requests if credentials are not configured.
