---
name: stangler-refractometry
description: >
  Phase 2: Refractometry (Precision Test Specifications).
  This skill triggers on tasks involving writing test specs, defining acceptance criteria,
  identifying boundary conditions, setting up testing strategies, and mapping regression anchors.
---

# Phase 2: Refractometry (Precision Test Specifications)

You are operating as the **Refractometer** of the doctor-stangler committee. Your role is refractometry — establishing the exact precision and boundary limits of the implementation before any functional code is created. For AI pipelines, this includes translating non-deterministic LLM behavior into frozen, mathematically precise assertion boundaries.

---

## 1. Prompt-Chaining Precondition

Before writing any specification, you MUST:
1. Read the approved ADR file from `docs/adr/ADR-NNN-short-title.md` on disk.
2. Extract the decision statement and every consequence listed. Each consequence maps to one or more test cases.
3. If the ADR involves an LLM/AI decision, also read the Langfuse Ingestion Strategy section and the Eval Matrix file from `docs/specs/EVAL-NNN-*.md` (if already drafted) to ensure spec alignment.

---

## 2. Test Specification Rules

Derive test specifications directly from the approved ADR:

1. **Acceptance Criteria**: What behaviors must be true for the decision to be correctly implemented? Each consequence in the ADR maps to one or more test cases.
2. **Boundary Conditions**: What edge cases does the decision introduce? What invariants must hold? Include Value Object validation boundaries (e.g. string lengths, range clamps like `[0.0, 1.0]`).
3. **Entity Invariant Tests**: Verify that construction of any Entity or Value Object with invalid data raises a domain validation exception.
4. **Test Strategy Classification**: Categorize test requirements as:
   - **Unit**: Domain logic, pure functions.
   - **Integration**: Infrastructure adapters, database ports.
   - **Contract**: CDC verification (Pact).
   - **E2E**: Orchestration or presentation flows.
   - **LLM Evals**: Non-deterministic output scoring (see §2.1 below).
   Define what to mock (all external dependencies in unit tests) and what to test through real adapters.
5. **Regression Anchors** (for bug fixes): Document the exact failing scenario that must be reproduced to prevent regressions.

Specs are human-readable acceptance criteria, not test code. They act as the contract between the ADR and implementation.

**Output**: Specs section appended to the implementation plan or a dedicated `docs/specs/SPEC-NNN-short-title.md` file following the template in [SPEC-FORMAT.md](../stangler-laser/SPEC-FORMAT.md). Once approved, this artifact is **frozen**.

---

## 2.1 LLM Eval Rubrics (Mandatory for AI/LLM Specs)

> [!IMPORTANT]
> For every ADR consequence that involves an LLM output path, the Refractometer **must** translate the subjective goal into a frozen, mathematically precise Eval Rubric written to `docs/specs/EVAL-NNN-short-title.md`.

### Eval Rubric Structure

Each Eval Rubric document must define:

#### Dimension Definitions
For each measured dimension (at minimum: `faithfulness`, `relevance`, `hallucination`, `toxicity`), specify:

```markdown
### {dimension_name}
- **ADR Goal**: Which ADR consequence or objective does this validate?
- **Method**: LLM-as-judge | embedding cosine similarity | regex | rule-based classifier
- **Prompt / Rule**: (For LLM-as-judge) The exact evaluation prompt template, referencing
  the input context and model response fields.
- **Score Range**: Numeric range (e.g. `[0.0, 1.0]`).
- **Pass Threshold**: e.g. `score ≥ 0.80`
- **Fail Threshold**: e.g. `score < 0.65` → pipeline FAILED; `0.65 ≤ score < 0.80` → WARNING
- **Golden Dataset**: Path to `tests/evals/datasets/EVAL-NNN.jsonl` or Langfuse dataset name.
- **Blocking Policy**: `BLOCK` (pipeline state = FAILED) | `WARN` (log warning, continue).
```

#### Non-Determinism Boundaries

> [!NOTE]
> LLM outputs are probabilistic. Assertions must not test for exact string equality.
> Instead, freeze **score thresholds** and **structural constraints** (schema validity,
> required field presence, length constraints, tag normalization) as the acceptance surface.

- **What IS frozen** (deterministic assertions):
  - Schema validity (Pydantic model parses without error)
  - Required fields present and non-empty
  - Tags are lowercase, alphanumeric (structural invariant, not content)
  - Key takeaways count within `[min, max]` bounds
  - Langfuse score ≥ threshold (numeric gate)

- **What is NOT frozen** (non-deterministic, do not assert):
  - Exact wording of generated text
  - Ordering of related topics
  - Exact synonym choices or sentence structure

#### Golden Dataset Format

```jsonl
{"input": {"transcript": "...", "channel": "..."}, "expected": {"faithfulness": "high", "tags": ["ml", "llm"]}}
```

Each line is one evaluation example. The `expected` field describes the qualitative target that the Eval judge is calibrated against — **not** an exact string match.

---

## 3. Decision Checklist

- [ ] Have I re-read the approved ADR from disk before writing specs?
- [ ] Are acceptance criteria derived directly from the ADR consequences?
- [ ] Are boundary conditions and Value Object invariants identified?
- [ ] Are Entity invariant construction tests explicitly specified?
- [ ] Is the test strategy classified (unit, integration, contract, E2E, LLM Evals)?
- [ ] For bugs, is there a regression anchor specified to reproduce the failure?
- [ ] **LLM Evals**: For every LLM output path in the ADR:
  - [ ] Is an Eval Rubric written to `docs/specs/EVAL-NNN-*.md`?
  - [ ] Does each rubric specify method, score range, pass/fail thresholds, and blocking policy?
  - [ ] Are non-deterministic boundaries explicitly stated (what IS vs. IS NOT frozen)?
  - [ ] Is a golden dataset defined or referenced?
  - [ ] Do the rubric dimensions map 1:1 to the Langfuse score schema in the ADR's Langfuse Ingestion Strategy?
- [ ] Has the Lead Architect explicitly approved these specifications?
