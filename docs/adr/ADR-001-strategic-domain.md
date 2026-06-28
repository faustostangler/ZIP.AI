# ADR-001: Strategic Domain Definition & Hexagonal Architecture Setup

**Status:** Accepted
**Date:** 2026-06-09
**Decision Makers:** stangler, AI implementer

## Context

We need a structured way to clean and categorize Gmail inbox emails using local LLMs (Ollama) while ensuring code maintainability, testability, and resilience. 
If business rules are directly coupled with Google APIs or Ollama HTTP protocols, any API change breaks the domain rules. We must decouple Regras de Negócio from infrastructure.

We will use terms defined in `docs/GLOSSARY.md` like `Email`, `ClassificationResult`, and `EmailAction`.

## Decision

We will implement a Modular Monolith using Domain-Driven Design (DDD) and Hexagonal Architecture (Ports and Adapters) because:
1. Isolating the domain layer prevents external API or LLM changes from corrupting core email sorting logic.
2. Interface-driven ports enable easy unit testing and mocking of I/O boundaries.

## Consequences

### Positive
*   Domain models (`Email`, `ClassificationResult`) are pure Python + Pydantic, decoupled from Gmail API client and httpx.
*   Unit tests for `ProcessInboxUseCase` can run hermetically using mock adapters.
*   We can swap Ollama for another LLM API (e.g., Gemini) by changing only the adapter, leaving use cases untouched.

### Negative
*   Introduces translation boilerplate (mapping API payloads to domain models).
*   Requires interface defining (Ports) before implementation.

### Neutral
*   Folder structure setup under `src/domain`, `src/ports`, `src/adapters` must be strictly enforced.

## Alternatives Considered

### Alternative A: Transactional Direct Script
*   **Pros:** Quick to build.
*   **Cons:** Untestable, high coupling, breaks on API modifications.
*   **Why rejected:** Fails Developer Experience (DX) and reliability goals of the workspace.

### Alternative B: Django/FastAPI-coupled Monolith
*   **Pros:** Built-in ORM/task runner tools.
*   **Cons:** Framework dependencies pollute domain entities.
*   **Why rejected:** We want zero framework dependencies in the domain.

## Compliance

- [x] Hexagonal Architecture layers respected
- [x] No framework dependencies in Domain layer
- [x] Tests strategy defined
- [x] Observability plan included
- [x] LGPD/Security implications assessed

## References

- Glossary: `docs/GLOSSARY.md`
- Project layout: `references/project_layout.md`
- Clean Code Standards: `references/37-DevOps, DDD, TDD, ADRs, Code.md`
