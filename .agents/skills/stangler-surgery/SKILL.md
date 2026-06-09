---
name: stangler-surgery
description: >
  Phase 3: Surgery (High-Performance Implementation & TDD).
  This skill triggers on tasks involving implementing code, writing unit or integration tests,
  refactoring, applying Hexagonal/Clean Architecture, setting up Pydantic/SQLAlchemy adapters,
  and executing TDD Red-Green-Refactor cycles.
---

# Phase 3: Surgery (High-Performance Implementation)

You are operating as the **Surgeon** of the doctor-stangler committee. Your role is surgical execution — implementing the specifications using Test-Driven Development (TDD) and clean Hexagonal Architecture. For AI pipelines, every generative process must be wrapped inside a Langfuse telemetry span, exposing all metadata required for Eval scoring.

---

## 1. Prompt-Chaining Preconditions

Before writing any code or tests:
1. **Pre-read Approved Specs**: Read the approved Specs artifact (`docs/specs/SPEC-NNN-*.md` or from implementation plan) from disk.
2. **Pre-read Approved ADR**: Read the approved ADR (`docs/adr/ADR-NNN-*.md`) from disk.
3. **Pre-read Eval Rubrics** (if ADR involves LLM): Read `docs/specs/EVAL-NNN-*.md` from disk to understand what metadata must be captured during implementation.
4. **Pre-read Reference Manuals**:
   - If wrapping legacy code, read [legacy_strangling_patterns.md](../stangler-doctor/references/legacy_strangling_patterns.md) to ensure correct Anti-Corruption Layer (ACL) boundaries.
   - If writing database migrations/schema updates, read [zero_downtime_migrations.md](../stangler-doctor/references/zero_downtime_migrations.md) to ensure lock minimization and Expand-Contract compliance.

---

## 2. Surgical Execution Steps (TDD Protocol)

### Pre-run Baseline Verification
Run `[ENV_EXEC] [TEST_EXEC]` to ensure the baseline test suite is clean and passing.

### Step 1: Skeleton Structure & Walkthrough Commenting
Create target `src/` files — modules, classes, and method signatures — using skeleton stubs (e.g. `raise NotImplementedError` or placeholder returns).
Spread walkthrough comments explaining implementation logic precisely where real code will live. **No functional code is allowed at this stage.**

### Step 2: Write Failing Tests
Write the test files in `tests/` based on the approved specifications.
- Tests must be pure and hermetic — mock all external dependencies.
- For bug fixes: write a regression test reproducing the exact failure.
- Ensure each test traces back to a specific numbered spec item.

### Step 3: Red State Verification
Execute `[ENV_EXEC] [TEST_EXEC]` to verify that the new tests fail as expected (guaranteeing a clean Red state).

### Step 4: Green Phase (Minimum Implementation)
Implement the **minimum code** required to make all tests pass (Green).
Execute `[ENV_EXEC] [TEST_EXEC]` to ensure all tests are green.

### Step 5: Refactor to Clean Standards
Refactor the implementation to meet Hexagonal Architecture and Clean Code guidelines:
- **Comments & Docstrings**: Inline comments are mandatory only for complex business rules, non-obvious algorithms, ACL boundaries, infrastructure limits, and exception reasoning. Keep self-explanatory boilerplate clean of comments. Write docstrings in Google Style.
- **Import Hygiene**: NEVER use `src.` prefixes in imports within `src/` (e.g. use relative imports or sibling paths).
- **Configuration**: Centralize all environment parameters in `.env` and validate with `pydantic-settings` in `config.py` (fail-fast principle).
- **Strict Typing**: Ensure rigorous type hints are added to all function signatures and class attributes. Avoid `Any`. Use `Final` or `Protocol` where appropriate.

---

## 2.1 LLM Adapter Implementation Rules (Langfuse Integration — Mandatory)

> [!CAUTION]
> **Every LLM adapter in `infrastructure/` MUST be instrumented with the Langfuse SDK. Uninstrumented LLM calls are architectural violations.**

### Required Langfuse Wrapping Pattern

Every LLM adapter method that makes a generative call must follow this pattern:

```python
# infrastructure/adapters.py — Langfuse-wrapped LLM adapter
import langfuse
from langfuse import Langfuse
from langfuse.decorators import observe, langfuse_context

class OllamaLLMAdapter(LLMPort):
    def __init__(self, base_url: str, model_name: str) -> None:
        # Step 1: Initialize Langfuse client for trace lifecycle management.
        # Why: Langfuse captures prompt versions, inputs, outputs, latency, and
        # token usage — enabling non-deterministic output scoring via Evals.
        self._langfuse = Langfuse()  # reads LANGFUSE_* env vars via pydantic-settings
        self.base_url = base_url
        self.model_name = model_name
        self.client = httpx.Client(timeout=60.0)

    @observe(as_type="generation")
    def synthesize_wiki(
        self,
        raw_note: RawNote,
        existing_articles: list[WikiArticle],
        *,
        trace_id: str | None = None,
        session_id: str | None = None,
        user_id: str | None = None,
    ) -> SynthesizedArticleSchema:
        # Step 2: Bind trace context metadata before the generative call.
        # Why: trace_id links this generation to the pipeline run (ContentId),
        # session_id groups all steps of a single pipeline execution,
        # user_id enables per-source telemetry aggregation.
        langfuse_context.update_current_trace(
            trace_id=trace_id or str(raw_note.content_id),
            session_id=session_id,
            user_id=user_id,
            tags=["synthesis", "wiki", self.model_name],
        )

        # Step 3: Retrieve the versioned prompt from Langfuse prompt registry.
        # Why: prompt_version links this generation to the exact prompt text
        # that produced the output, enabling reproducibility and A/B evaluation.
        prompt = self._langfuse.get_prompt(
            name="wiki-synthesis-v1",
            version=None,  # latest; pin to version int in production
        )
        rendered_prompt = prompt.compile(
            channel_name=raw_note.metadata.channel_name,
            title=raw_note.title,
            content=raw_note.transcript_text,
        )

        # Step 4: Bind model name and rendered prompt to the current generation span.
        langfuse_context.update_current_observation(
            model=self.model_name,
            input=rendered_prompt,
        )

        # Step 5: Execute the LLM call.
        response = self.client.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model_name, "prompt": rendered_prompt, "format": "json", "stream": False},
        )
        response.raise_for_status()
        response_text = response.json().get("response", "")

        # Step 6: Bind output and token metadata to the current generation span.
        # Why: Output binding is required for Langfuse Eval scoring — the evaluator
        # reads `output` from the span to compute faithfulness and relevance scores.
        langfuse_context.update_current_observation(
            output=response_text,
            usage={"input": len(rendered_prompt.split()), "output": len(response_text.split())},
        )

        return SynthesizedArticleSchema(**json.loads(response_text))
```

### Execution Metadata Requirements

The following metadata MUST be captured as Langfuse span data for every generative call:

| Metadata Field | Source | Langfuse Field |
|---------------|--------|----------------|
| `trace_id` | `ContentId` of the processing entity | `trace_id` |
| `session_id` | Pipeline run ID (timestamp or UUID) | `session_id` |
| `user_id` | Source channel / operator ID | `user_id` |
| `model` | `settings.OLLAMA_MODEL` | `model` |
| `prompt_name` + `prompt_version` | Langfuse Prompt Registry | `input` metadata |
| `input` | Full rendered prompt string | `input` |
| `output` | Raw LLM response string | `output` |
| `latency_ms` | Auto-captured by `@observe` decorator | `latency` |
| `token_count` | Word/token estimate or API response | `usage` |

### Pydantic-Settings Config Extension

Add these fields to `config.py` for Langfuse credentials:

```python
# config.py — Langfuse observability settings
LANGFUSE_SECRET_KEY: str = Field(default="", description="Langfuse secret key")
LANGFUSE_PUBLIC_KEY: str = Field(default="", description="Langfuse public key")
LANGFUSE_HOST: str = Field(default="https://cloud.langfuse.com", description="Langfuse host URL")
```

---

## 3. Reference and Decision Checklist

### References
- Refer to [project_layout.md](../stangler-doctor/references/project_layout.md) to verify directory structure.

### Checklist
- [ ] Have I re-read the approved Specs and ADR from disk before starting?
- [ ] If the ADR involves LLM, have I read the Eval Rubrics from `docs/specs/EVAL-NNN-*.md`?
- [ ] Am I writing tests FIRST (TDD) before implementing functional logic?
- [ ] Do tests run and fail in a clean Red state?
- [ ] Does the skeleton use stubs and walkthrough comments before implementation?
- [ ] Are inline comments restricted to complex code, ACL boundaries, or algorithms?
- [ ] Is all I/O isolated behind Ports & Adapters interfaces (ABCs/Protocols)?
- [ ] Are domain models strictly segregated from persistence/ORM models?
- [ ] Is config configured in `.env` and validated using Pydantic Settings?
- [ ] Are Google Style docstrings and strict type hints applied without using `Any`?
- [ ] Does the code build and pass `[ENV_EXEC] [TEST_EXEC]` successfully?
- [ ] **LLM Adapters**: Is the Langfuse client initialized in `__init__` using env vars from `pydantic-settings`?
- [ ] **LLM Adapters**: Is every generative call decorated with `@observe(as_type="generation")`?
- [ ] **LLM Adapters**: Are `trace_id`, `session_id`, `user_id`, and contextual tags bound via `langfuse_context.update_current_trace()` before the call?
- [ ] **LLM Adapters**: Is the prompt retrieved from the Langfuse Prompt Registry (versioned) rather than hardcoded?
- [ ] **LLM Eval Metadata**: Are `input`, `output`, `model`, and `usage` bound to the span via `langfuse_context.update_current_observation()`?
