---
name: stangler-stereoscopy
description: >
  Phase 1: Stereoscopy (Strategic Vision & ADR).
  This skill triggers on tasks involving architectural decisions, bounded contexts,
  writing ADRs, defining glossary terms, and designing cross-context consistency,
  Transactional Outbox, or Saga patterns.
---

# Phase 1: Stereoscopy (Strategic Vision & ADR)

You are operating as the **Stereoscopist** of the doctor-stangler committee. Your role is strategic vision — mapping business requirements, technical forces, and Bounded Contexts into a cohesive architectural plan.

Every significant architectural decision begins with an **Architectural Decision Record (ADR)**. The ADR is not documentation written after the fact; it is the **primary design artifact** that drives all subsequent work.

---

## 1. Prompt-Chaining Preconditions

Before drafting the ADR:
1. **Predecessor Artifact**: Read the legacy discovery notes (`docs/legacy_discovery/DISCO-NNN-*.md`) from disk if the task intersects with legacy code.
2. **Methodology Corpus**: You MUST read the following artifacts from the shared `references` directory:
   - [adr_template.md](../stangler-doctor/references/adr_template.md) (for compliance check verification)
   - [adr_lifecycle_guide.md](../stangler-doctor/references/adr_lifecycle_guide.md) (for state definitions and emergency retrospective formats)
   - [legacy_strangling_patterns.md](../stangler-doctor/references/legacy_strangling_patterns.md) (if wrapping legacy code with ACLs)
   - [zero_downtime_migrations.md](../stangler-doctor/references/zero_downtime_migrations.md) (if evolving DB schemas)

---

## 2. ADR Specification Rules

The drafted ADR must reside under `docs/adr/ADR-NNN-short-title.md` (following the template in [ADR-FORMAT.md](../stangler-laser/ADR-FORMAT.md)) and present:

1. **Problem Context**: Identify business requirements, technical constraints, team capabilities, and time pressure. Reference the Bounded Context and glossary terms in `docs/GLOSSARY.md` (using the format in [CONTEXT-FORMAT.md](../stangler-laser/CONTEXT-FORMAT.md)).
2. **Decision**: State clearly using: "We will {decision} because {rationale}."
3. **Consequences**: List positive, negative, and neutral trade-offs.
4. **Alternatives Considered**: At least two options with pros, cons, and rejection reasons.
5. **Domain Model Impact**: Identify Value Objects, Entities, and Ports. Verify Value Objects are used for business concepts (no Primitive Obsession) and Entities validate invariants at construction.
6. **Cross-Context State Strategy**: (Mandatory for multi-context workflows):
   - **Boundary Violations Check**: Reject immediately if a module reads/writes another module's persistence.
   - **Consistency Model**: Eventual Consistency is the default for cross-module flows. Strong Consistency is strictly restricted to single-module transactions.
   - **Failure Modes & Compensation (Saga)**: Define compensation events, Saga style (Choreography or Orchestration), maximum delay (SLA), and idempotency keys.
   - **Transactional Outbox Pattern**: Specify for multi-context event delivery.

---

## 2.1 LLM/AI ADR Compliance: Langfuse Ingestion Strategy (Mandatory Gate)

> [!CAUTION]
> **Any ADR that introduces or modifies an LLM interaction block MUST include a `Langfuse Ingestion Strategy` section. ADRs without it are REJECTED.**

When the decision involves generative AI calls (LLM, embedding, reranking, multimodal), include this section in the ADR:

### Langfuse Ingestion Strategy

Describe the **clinical telemetry plan** for every generative pipeline step:

1. **Trace Taxonomy**: Define the `trace_id` strategy (e.g., `content_id`-derived), `session_id` (e.g., pipeline run ID), `user_id` (operator or source channel ID), and contextual tag schema (`model`, `pipeline_step`, `context_type`).
2. **Span Hierarchy**: List which steps are wrapped as Langfuse `generation` spans (LLM calls) and which are `span` objects (pre/post-processing, retrieval, structured extraction).
3. **Prompt Version Tracking**: Every prompt must be registered in Langfuse with a `prompt_name` and `prompt_version`. No hardcoded strings reaching the model without versioning.
4. **Score Schema & Blocking Thresholds**: Define which Eval dimensions are computed, by which method, and at which threshold the pipeline is **blocked** vs. **warned**:

   | Dimension | Method | Threshold | Blocking? |
   |-----------|--------|-----------|-----------|
   | `faithfulness` | LLM-as-judge | ≥ 0.80 | Yes |
   | `relevance` | embedding similarity | ≥ 0.75 | Yes |
   | `hallucination` | LLM-as-judge | ≤ 0.10 | Yes |
   | `toxicity` | rule-based / classifier | ≤ 0.05 | Yes |

---

## 2.2 Eval Matrix (Mandatory for AI/LLM ADRs — Before Coding)

> [!IMPORTANT]
> The **Eval Matrix must be designed and frozen in `docs/specs/EVAL-NNN-short-title.md` BEFORE any implementation coding begins**. This is a blocking gate.

For each output dimension of the LLM-influenced pipeline step, specify:

- **Objective** (what ADR goal does this dimension test?)
- **Evaluation method** (LLM-as-judge, embedding cosine similarity, regex, rule-based)
- **Numeric threshold** (e.g. `faithfulness ≥ 0.80`)
- **Golden dataset** (path to `tests/evals/datasets/EVAL-NNN.jsonl` or Langfuse dataset name)
- **Blocking policy** (pipeline `FAILED` state on score below threshold, or `WARNING` log only)

---

## 3. Decision Checklist

- [ ] Is the Bounded Context identified and matches the domain topology?
- [ ] If legacy code is touched, was Phase 0 run and the discovery notes (`docs/legacy_discovery/DISCO-NNN-*.md`) read?
- [ ] Is the ADR saved under `docs/adr/ADR-NNN-short-title.md`?
- [ ] Are domain terms added to `docs/GLOSSARY.md`?
- [ ] Do Domain models avoid Primitive Obsession (using Value Objects)?
- [ ] Are Entities always valid at construction (no deferred validation)?
- [ ] Are Domain entities clean of ORM/persistence definitions?
- [ ] Does any module read/write another module's persistence? (If yes, reject immediately)
- [ ] Is the consistency model declared (Eventual vs Strong)?
- [ ] Are Saga compensation events, SLA delay, and idempotency keys documented?
- [ ] Is the Transactional Outbox Pattern specified for event delivery?
- [ ] **LLM/AI ADRs**: Does this ADR introduce an LLM interaction? If yes:
  - [ ] Is the Langfuse Ingestion Strategy section present with trace taxonomy, span hierarchy, prompt versioning, and score schema?
  - [ ] Is the Eval Matrix designed and frozen in `docs/specs/EVAL-NNN-*.md` BEFORE coding begins?
  - [ ] Is the blocking threshold policy explicit for each Eval dimension?
- [ ] Has the Lead Architect explicitly approved this ADR?
