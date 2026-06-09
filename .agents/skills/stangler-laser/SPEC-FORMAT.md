# Spec Format

Test specifications (Specs) are the frozen, human-readable contract between an approved ADR and the implementation. They live in `docs/specs/` and use sequential numbering: `SPEC-NNN-slug.md` (e.g., `SPEC-001-slug.md`, `SPEC-002-slug.md`, etc.), matching the corresponding `ADR-NNN-slug.md`.

Create the `docs/specs/` directory lazily — only when the first specification is drafted.

---

## Template

```markdown
# SPEC-{NNN}: {Short Title}

**Linked ADR:** [ADR-{NNN}](../adr/ADR-{NNN}-slug.md)
**Status:** Draft | Approved | Frozen | Superseded by SPEC-{NNN}
**Date:** YYYY-MM-DD
**Bounded Context:** {Context Name (e.g., Ordering, Billing)}

## 1. Overview & Objectives

Briefly describe the capability being specified and the key behaviors derived from [ADR-{NNN}](../adr/ADR-{NNN}-slug.md).

## 2. Bounded Context & Domain Invariants

Define the domain boundaries, Entities, and Value Objects involved, and their constraints/invariants:
- **Entity**: `{EntityName}` (e.g., `Order`)
  - Invariant: `{Invariant Description}` (e.g., Total amount must be non-negative)
- **Value Object**: `{ValueObjectName}` (e.g., `EmailAddress`)
  - Validation: `{Regex or parsing rule}` (e.g., must match standard email pattern)

## 3. Test Strategy Classification

Categorize testing requirements into the standard architecture layers:

- **Unit Tests (Domain & Ports)**:
  - Scope: Pure business logic, Value Object validation, Entity invariants.
  - Mock Boundary: All database adapters, network calls, external clock/time providers.
- **Integration Tests (Adapters & Infra)**:
  - Scope: Database operations (SQLAlchemy/PostgreSQL), Redis caching logic, HTTP client adapters.
  - Dependencies: Real docker-test database instances, redis instances. No external API calls.
- **Contract Tests (CDC)**:
  - Scope: Cross-context contracts using Pact.
- **E2E / Orchestration Tests**:
  - Scope: API controllers, FastAPI routes, and request validation.
- **LLM Evals (Non-Deterministic Gates)**:
  - Scope: Output of LLM/generative steps verified against eval rubrics (link to [EVAL-NNN-slug.md](./EVAL-NNN-slug.md)).

## 4. Acceptance Criteria (Scenarios)

Write the precise scenarios using a BDD-style (Given-When-Then) structure where applicable. Each scenario must correspond directly to a consequence in the ADR.

### Scenario 1: {Successful Flow Description}
- **Given**: {initial state / inputs}
- **When**: {action is executed}
- **Then**: {expected outcome / state mutation}

### Scenario 2: {Failure / Boundary Condition}
- **Given**: {initial state / inputs}
- **When**: {invalid action or input is provided}
- **Then**: {specific domain validation error is raised}

## 5. Boundary Conditions & Exception Mapping

Map specific inputs to the precise exceptions they must raise:

| Input Field | Input Value / Boundary | Expected Exception / Error Code |
|-------------|-------------------------|---------------------------------|
| `amount`    | `< 0.0`                 | `NegativeAmountError`           |
| `email`     | `invalid-email`         | `InvalidEmailFormatError`       |

## 6. Regression Anchors (For Bug Fixes Only)

*If this spec is for a bug fix/reproduction:*
- **Failing Test Case**: Define the exact conditions to reproduce the reported bug.
- **Verification**: The test must fail on the current main/production code (Red) and pass once the fix is implemented (Green).

## 7. Observability & Telemetry Assertions

- **Langfuse Spans**:
  - Assert that a trace is generated with name `{trace_name}`.
  - Assert metadata includes: `session_id`, `user_id`, and `version`.
- **Prometheus Metrics**:
  - Assert that `{metric_name}` counter is incremented by 1 on success/failure.
- **Sentry Integration**:
  - Assert that unhandled domain errors are logged with warning/error severity.
```

---

## LLM Eval Rubric Template (EVAL-NNN)

If the ADR consequences involve generative AI (LLM pipelines, embeddings, etc.), create a matching evaluation rubric in `docs/specs/EVAL-NNN-slug.md`.

```markdown
# EVAL-{NNN}: {LLM Pipeline Name} Rubric

**Linked SPEC:** [SPEC-{NNN}](./SPEC-{NNN}-slug.md)
**Blocking Policy:** BLOCK (fails the pipeline on threshold breach) | WARN (log warning only)

## Dimensions

### 1. Faithfulness
- **ADR Consequence**: {consequence ID / reference}
- **Method**: LLM-as-judge
- **Prompt Template**:
  ```
  [System Prompt for Eval Judge]
  ```
- **Score Range**: `[0.0, 1.0]`
- **Pass Threshold**: `score >= 0.80` (BLOCK)

### 2. Relevance
- **ADR Consequence**: {consequence ID / reference}
- **Method**: Cosine similarity against reference embedding
- **Pass Threshold**: `score >= 0.75` (WARN)
- **Dataset**: `tests/evals/datasets/EVAL-{NNN}.jsonl`
```
