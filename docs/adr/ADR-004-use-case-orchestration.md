# ADR-004: Use Case Orchestration & Mock Testing Strategy

**Status:** Proposed
**Date:** 2026-06-09
**Decision Makers:** stangler, AI implementer

## Context

We need an orchestration component (`ProcessInboxUseCase`) to coordinate inbox cleanup without exposing orchestration logic directly to adapters (Gmail, Ollama). 
To make it highly maintainable and robust against regression, we need complete isolation and mock-based testing of dependencies.

This maps to `ProcessInboxUseCase` in the Bounded Context.

## Decision

We will implement `ProcessInboxUseCase` to coordinate Gmail API calls and LLM analysis using explicit Dependency Injection of `GmailPort` and `LLMPort` implementations. 

"We will orchestrate inbox processing using a unified usecase constructor injecting interfaces because it isolates orchestrator behavior from concrete infrastructure dependencies, making it simple to write isolated unit tests."

## Consequences

### Positive
*   Pure application orchestration decoupled from Gmail Client and HTTP clients.
*   Fast, reliable, and decoupled unit tests (no network access required).
*   Allows swapping concrete implementations easily (e.g., testing with stub adapters).

### Negative
*   Requires manual wiring of ports and adapters in the CLI entry point (`cli.py`).

### Neutral
*   Usecase execution returns a list of classification results to the caller for reporting.

## Alternatives Considered

### Alternative A: Direct instantiation of adapters in usecase
*   **Pros:** Less boilerplate.
*   **Cons:** Hard-couples usecase to `GmailOAuthAdapter` and `OllamaLLMAdapter`, preventing unit testing.
*   **Why rejected:** Violates Hexagonal Architecture principles.

### Alternative B: Event-driven inbox processing
*   **Pros:** More reactive.
*   **Cons:** Over-engineered for a simple CLI tool running on demand.
*   **Why rejected:** Simple sequential orchestration is sufficient and matches the KISS principle.

## Compliance

- [x] Hexagonal Architecture layers respected
- [x] No framework dependencies in Domain layer
- [x] Tests strategy defined
- [x] Observability plan included
- [x] LGPD/Security implications assessed

## References

- Use Case: `src/domain/use_cases.py`
- Tests: `tests/unit/test_use_cases.py`
