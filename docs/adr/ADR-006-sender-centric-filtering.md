# ADR-006: Sender-Centric Email Filter Automation & Generic AI Integration

**Status:** Proposed
**Date:** 2026-06-28
**Decision Makers:** stangler, AI implementer

## Context

Our existing workflow is email-centric: it classifies individual emails and acts on them. However, for recurring newsletters and promotional emails, we want to permanently automate moving them out of the inbox by creating a Gmail filter for the sender. 

To prevent redundant processing and API limits, we need:
1. A **sender-centric workflow** that operates on unique senders.
2. A **local persistent registry** to track senders that have already been evaluated and processed.
3. A **generic AI port** capable of classifying sender histories using binary structured outputs across different providers (e.g. local Ollama or generic external APIs).
4. An **isolated Use Case** to maintain code modularity without breaking the legacy email-centric loop.

This maps to `Inbox Processing` and `LLM Categorization` Bounded Contexts.

## Decision

We will:
1. Define `ProcessedSendersPort` to manage local persistence of evaluated senders.
2. Implement `JsonProcessedSendersAdapter` using atomic file writes to read and store processed sender emails in a local JSON file.
3. Expand `LLMPort` and implement `GenericLLMAdapter` that accepts a list of historical emails and returns a boolean value (`True` if the pattern matches a newsletter, `False` otherwise) using structured JSON output.
4. Implement `ProcessSenderCentricFiltersUseCase` under `src/domain/use_cases.py` to coordinate the new sender-centric filter automation loop.

```
+--------------------+
|  Use Case:         |
|  ProcessSender-    |
|  CentricFilters    |
+---------+----------+
          |
          +---------> [Port] ProcessedSendersPort <--- [Adapter] JsonProcessedSendersAdapter
          |
          +---------> [Port] LLMPort             <--- [Adapter] GenericLLMAdapter
          |
          +---------> [Port] GmailPort           <--- [Adapter] GmailOAuthAdapter
```

"We will create a new isolated Use Case and local JSON-based state registry because it decouples the new sender-centric logic from legacy flows, ensures we evaluate each sender only once, and allows us to swap LLM providers easily using a generic interface."

## Consequences

### Positive
*   **Performance & Efficiency**: We only process each sender once, saving API tokens and Gmail API calls.
*   **Modularity**: High cohesion and low coupling by keeping the new logic in an isolated use case (respects Open-Closed Principle).
*   **Structured Output Safety**: Binary output schema prevents fragile parsing.
*   **Flexibility**: Generic AI adapter enables swapping between Ollama and third-party API providers easily.

### Negative
*   **State Dependency**: Local JSON file state must be maintained. If deleted/corrupted, previously processed senders will be re-processed.
*   **Concurrency**: Multiple concurrently running processes could cause race conditions on the JSON file (which we mitigate with safe file writes).

### Neutral
*   Filters are created on a per-sender basis, matching existing safety paradigms.

---

## Langfuse Ingestion Strategy

We instrument the new AI pipeline with Langfuse telemetry:

1.  **Trace Taxonomy**:
    *   `trace_id`: Derived from the target sender's email address hash.
    *   `session_id`: UUID generated per workflow execution run.
    *   `user_id`: gmail user ("me").
    *   `tags`: `["workflow:sender-centric", "provider:generic-llm"]`.
2.  **Span Hierarchy**:
    *   `Span: compile-history`: Formats sender emails list into prompt.
    *   `Generation: classification`: Calls the LLM with structured output schema.
3.  **Prompt Version Tracking**:
    *   Prompt registered as `zip-sender-newsletter-classifier`.
4.  **Score Schema & Blocking Thresholds**:

| Dimension | Method | Threshold | Blocking? |
|-----------|--------|-----------|-----------|
| `relevance` | rule-based | - | No |
| `faithfulness` | LLM-as-judge | ≥ 0.80 | Yes |

---

## Alternatives Considered

### Alternative A: SQLite Storage
*   **Pros:** Thread-safe, easily scalable for millions of senders.
*   **Cons:** Overkill for single-user inbox operations.
*   **Why rejected:** A simple JSON store satisfies the KISS principle and has zero local database setup requirements.

### Alternative B: Directly updating the current Use Case
*   **Pros:** Single use case class to maintain.
*   **Cons:** Increases complexity of the existing unread-loop class, violating Single Responsibility Principle.
*   **Why rejected:** Keeps workflows isolated to make testing cleaner and support fallback scenarios.

## Compliance

- [x] Hexagonal Architecture layers respected
- [x] No framework dependencies in Domain layer
- [x] Tests strategy defined
- [x] Observability plan included
- [x] LGPD/Security implications assessed

## References

- Use Case: `src/domain/use_cases.py`
- Ports: `src/ports/processed_senders.py`, `src/ports/llm.py`
- Adapters: `src/adapters/json_processed_senders.py`, `src/adapters/generic_llm_adapter.py`
