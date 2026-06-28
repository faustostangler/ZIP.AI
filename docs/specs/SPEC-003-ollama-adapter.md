# SPEC-003: Ollama LLM Adapter Test Specification

This document details the test scenarios and invariants for the `OllamaLLMAdapter`.

## Acceptance Criteria

### 1. Classification Request Formatting (`classify_email`)
*   **SPEC-003.1**: Submits payload to Ollama `/api/chat` with:
    *   Target model set to `Settings.ollama_model`.
    *   Temperature set to `0.0` (deterministic options).
    *   `format` parameter containing the correct JSON schema for `ClassificationResult`.
    *   `stream` set to `False`.
*   **SPEC-003.2**: Truncates the email body to 1500 characters to prevent context window overflow.
*   **SPEC-003.3**: Prompt contains email ID, sender, subject, and ISO format of received date.

### 2. Response Parsing & Fallbacks
*   **SPEC-003.4**: Successfully parses Ollama's HTTP JSON response containing the structured model decision and maps it to a `ClassificationResult`.
*   **SPEC-003.5**: Overrides the returned `email_id` in the result with the original email ID to guarantee integrity.
*   **SPEC-003.6**: If Ollama service fails (HTTP errors, timeouts, connection issues, or schema validation failures), catches the error and degrades gracefully:
    *   Returns a fallback `ClassificationResult` with `action=EmailAction.NONE`.
    *   Sets `reason` to describe the failure context.

## Test Strategy

*   **Unit & Integration Tests**: Test mock HTTPX responses to simulate successful JSON returns, schema invalidation, and server HTTP connection crashes.
*   **Telemetry Verification**: Verify that Langfuse client traces can be created during execution (if enabled).
