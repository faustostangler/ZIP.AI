# ADR-005: Commercial/Spam Sender Filter Automation

**Status:** Accepted
**Date:** 2026-06-09
**Decision Makers:** stangler, AI implementer

## Context

When a sender sends commercial/promotional emails or spam repeatedly, we want to automate moving their future messages out of the inbox. 
To do this reliably, we must first verify if a sender has a pattern of commercial/spam emails by looking at their past messages.
If verified, we want to automatically create a Gmail filter that marks as read and deletes (moves to trash) future messages from that sender.

## Decision

We will extend `GmailPort` and `LLMPort` interfaces and modify `ProcessInboxUseCase` to:
1. Identify high confidence commercial or spam emails.
2. Query Gmail API for all messages from that sender.
3. Use Ollama to verify if the collection of messages represents a commercial pattern.
4. If verified, create a Gmail filter utilizing `users.settings.filters.create` with criteria `from: sender` and action `removeLabelIds: ['UNREAD', 'INBOX']` and `addLabelIds: ['TRASH']`.

"We will query past emails from the sender and verify the commercial pattern using the LLM before creating a filter because it prevents false-positive filter creation on occasional non-commercial messages."

## Consequences

### Positive
*   Automated, zero-maintenance inbox cleanup for recurring commercial/spam senders.
*   Pattern verification minimizes false positive filter creations (e.g. transactional emails from a business that also sends marketing).

### Negative
*   Requires additional Gmail API scope: `"https://www.googleapis.com/auth/gmail.settings.basic"`.
*   Adds network latency due to extra email fetching and LLM analysis when triggering filter checks.

### Neutral
*   Filters are created on a per-sender basis for simplicity and safety.

## Alternatives Considered

### Alternative A: One filter to rule them all (Consolidated Filter)
*   **Pros:** Clean filter list in Gmail UI.
*   **Cons:** Updating a filter requires deletion and recreation since Gmail settings API does not support updates. This risks concurrency issues and character limits.
*   **Why rejected:** High complexity and fragility. Per-sender filters are safer.

### Alternative B: Direct filter creation on first email classification
*   **Pros:** No need to fetch past emails or run verification.
*   **Cons:** High risk of false positives.
*   **Why rejected:** A single commercial classification shouldn't permanently ban a sender. Verification ensures a persistent commercial pattern.

## Compliance

- [x] Hexagonal Architecture layers respected
- [x] No framework dependencies in Domain layer
- [x] Tests strategy defined
- [x] Observability plan included
- [x] LGPD/Security implications assessed

## References

- Port: `src/ports/gmail.py`
- Adapter: `src/adapters/gmail_adapter.py`
- Glossary: `docs/GLOSSARY.md`
