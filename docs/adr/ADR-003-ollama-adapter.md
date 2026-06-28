# ADR-003: Ollama Local LLM Adapter & Telemetry Integration

**Status:** Proposed
**Date:** 2026-06-09
**Decision Makers:** stangler, AI implementer

## Context

We need a categorization engine that maps an email's content to a discrete `EmailAction` (Archive, Delete, Label, None).
We are running a local Ollama instance with a model of up to 6GB VRAM (e.g., `llama3:latest`). Because LLM outputs are non-deterministic, we need structured outputs (JSON schema constraints) and telemetry to trace prompts, latency, and evaluate accuracy.

This maps to `LLMPort` in the Bounded Context.

## Decision

We will implement `OllamaLLMAdapter` inheriting from `LLMPort` using `httpx` to communicate with the local Ollama API. We will configure structured JSON generation using the `/api/chat` endpoint's `format` parameter. We will instrument this with Langfuse for tracing and logging.

"We will interface with local Ollama using JSON schema validation and structured formats because it guarantees structured data mapping directly to `ClassificationResult` without fragile regex parsing."

## Consequences

### Positive
*   Guaranteed JSON output layout from Ollama, preventing JSON parsing failures.
*   Low latency and zero cost via local model inference.
*   Full clinical telemetry coverage of prompt templates and generation spans using Langfuse.

### Negative
*   Local inference performance (speed) depends directly on the system's hardware VRAM capacity.
*   Requires a running Ollama server instance at execution time.

### Neutral
*   Ollama requires temperature set to `0.0` to maximize determinism.

---

## Langfuse Ingestion Strategy

To ensure clinical observability, we instrument the LLM pipeline with Langfuse:

1.  **Trace Taxonomy**:
    *   `trace_id`: Derived from the `Email.id`.
    *   `session_id`: UUID generated per execution run of the CLI batch processor.
    *   `user_id`: gmail user ("me").
    *   `tags`: `["model:llama3", "pipeline:inbox-cleanup", "env:development"]`.
2.  **Span Hierarchy**:
    *   `Span: preprocess`: Handles body truncation (max 1500 chars) and system/user prompt formatting.
    *   `Generation: email-classification`: Captures the actual chat request/response, token usage, latency, and model configuration.
    *   `Span: postprocess`: Handles validation of the returned schema into `ClassificationResult`.
3.  **Prompt Version Tracking**:
    *   Prompt registered in Langfuse under `zip-email-classifier`.
    *   Version matches the current active template in Langfuse Registry.
4.  **Score Schema & Blocking Thresholds**:

| Dimension | Method | Threshold | Blocking? |
|-----------|--------|-----------|-----------|
| `relevance` | embedding similarity | ≥ 0.75 | Yes |
| `faithfulness` | LLM-as-judge | ≥ 0.80 | Yes |
| `hallucination` | LLM-as-judge | ≤ 0.10 | Yes |

---

## Alternatives Considered

### Alternative A: Raw Text output with regex parsing
*   **Pros:** Works on older LLM APIs that do not support structured JSON.
*   **Cons:** Highly fragile; LLM updates can break regex patterns.
*   **Why rejected:** Ollama natively supports JSON schema validation, which is far more robust.

### Alternative B: External SaaS API (Gemini / OpenAI)
*   **Pros:** Better reasoning capability.
*   **Cons:** Network latency, API cost, privacy issues (PII leaving local environment).
*   **Why rejected:** The project requires a local model up to 6GB VRAM to run offline and preserve email privacy.

## Compliance

- [x] Hexagonal Architecture layers respected
- [x] No framework dependencies in Domain layer
- [x] Tests strategy defined
- [x] Observability plan included
- [x] LGPD/Security implications assessed

## References

- Port: `src/ports/llm.py`
- Adapter: `src/adapters/ollama_adapter.py`
- Langfuse integration rules: `references/37-DevOps, DDD, TDD, ADRs, Code.md`
