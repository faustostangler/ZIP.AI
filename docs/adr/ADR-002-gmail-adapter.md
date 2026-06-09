# ADR-002: Gmail Adapter Implementation & OAuth2 Flow

**Status:** Proposed
**Date:** 2026-06-09
**Decision Makers:** stangler, AI implementer

## Context

We need to interface with the Google Gmail API to fetch unread emails and apply actions (Archive, Delete, Label). 
The integration requires OAuth2 credentials. We need robust error handling and token refresh mechanisms to prevent runtime auth failures.

This maps to `GmailPort` in the Bounded Context.

## Decision

We will implement `GmailOAuthAdapter` inheriting from `GmailPort` using the official Google API Python Client. It will load, refresh, and save tokens to `token.json` automatically, using credentials from `Settings`.

"We will encapsulate Google API calls within `GmailOAuthAdapter` because it isolates OAuth2 complexity and Google HTTP client dependencies from the core domain."

## Consequences

### Positive
*   Simplifies token management via standard `google-auth` library.
*   Enables automated refreshing of expired access tokens using the refresh token.
*   Clearly separated logic for extracting email text bodies recursively (`_extract_body`).

### Negative
*   Interactive OAuth flow (`run_local_server`) is not suitable for headless CI or daemon mode. We must allow file-based token seeding in those environments.
*   Exceptions from the Google library (`HttpError`) must be mapped to prevent infrastructure leaks.

### Neutral
*   `token.json` will be written to disk locally to persist session credentials.

## Alternatives Considered

### Alternative A: Raw HTTP client requests to Gmail REST API
*   **Pros:** Fewer dependencies.
*   **Cons:** Re-implementing OAuth2 token refresh and multipart parsing from scratch is highly error-prone.
*   **Why rejected:** We want to reuse robust standard library tools (`google-api-python-client`) for developer velocity and safety.

### Alternative B: Service Account auth
*   **Pros:** Non-interactive auth.
*   **Cons:** Gmail API domain-wide delegation is complex and poses high security risks for personal accounts.
*   **Why rejected:** Installed client OAuth2 flow is standard and safer for individual personal mailboxes.

## Compliance

- [x] Hexagonal Architecture layers respected
- [x] No framework dependencies in Domain layer
- [x] Tests strategy defined
- [x] Observability plan included
- [x] LGPD/Security implications assessed

## References

- Port: `src/ports/gmail.py`
- Adapter: `src/adapters/gmail_adapter.py`
- Domain: `src/domain/entities.py`
