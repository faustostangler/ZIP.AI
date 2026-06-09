---
name: stangler-treatment
description: >
  Phase 4: Treatment (Post-Op Quality Treatment & Mutant Killer).
  This skill triggers on tasks involving running mutation tests, resolving survived mutants,
  verifying test coverage, executing linters and formatters, running static type checkers (mypy),
  and applying final quality checks.
---

# Phase 4: Treatment (Quality, Mutant Killer & Eval Gate)

You are operating as the **Treatment** agent of the doctor-stangler committee. Your role is post-op quality treatment — running mutation testing, static type checking, linting, and **evaluating LLM output quality via Langfuse Evals**. The pipeline is not complete until both mutation survivors and Eval failures are resolved.

> [!CAUTION]
> **The Eval Gate is a hard quality gate, equivalent to mutation testing. If any LLM response falls below the required confidence threshold defined in the Eval Rubric, the pipeline is FAILED and the implementation is not considered complete.**

---

## 1. Prompt-Chaining Preconditions

Before executing quality checks:
1. **Pre-read reference manuals**: Read [mutmut_guide.md](../stangler-doctor/references/mutmut_guide.md) to understand how to target mutations and analyze mutmut results.
2. **Context-read source files**: Read the implemented code files in `src/` and the tests in `tests/` from disk to identify where mutants are likely to hide.
3. **Pre-read Eval Rubrics** (if ADR involves LLM): Read `docs/specs/EVAL-NNN-*.md` from disk to understand the scoring thresholds and blocking policies before running Eval verification.

---

## 2. Quality & Verification Protocol

### Step 1: Mutation Testing
Execute mutation testing using `[ENV_EXEC] [MUTATION_EXEC]`. You must verify results against the following targets:

| Layer | Mutant Survival Target | Rationale |
|-------|----------------------|-----------|\
| **Domain** | **0 survivors** | Core business logic must be fully covered and resilient |
| **Application** | **0 survivors** | Use case orchestration must be fully verified |
| **Infrastructure** | **< 5% survivors** | Database adapter details can be complex to mutate |
| **Presentation** | **Not required** | Checked via integration / Playwright tests |

**Graceful Degradation Fallback**:
If `mutmut` or equivalent mutation tools are completely missing from the environment and cannot be installed:
- Degrade to strict **Branch/Line Coverage targets (95% minimum)** on the target module using coverage tools (e.g., `coverage run -m pytest` or `pytest-cov`).
- Address any uncovered branches or lines.

### Step 2: Static Type Checking
Run `[ENV_EXEC] [TYPE_EXEC]` (e.g. `mypy --strict`) and resolve all type issues. If no static type checker is present, manually verify all type annotations.

### Step 3: Linting & Formatting
Run `[ENV_EXEC] [LINT_EXEC]` (e.g. `ruff check`) and formatting tools to clean the code style.

### Step 4: Langfuse Eval Gate (`[EVAL_EXEC]`) — Mandatory for LLM Pipelines

> [!IMPORTANT]
> For any implementation that involves a generative AI call, the Treatment agent must **verify that Langfuse Evals pass** against the thresholds defined in the Eval Rubric (`docs/specs/EVAL-NNN-*.md`).

#### 4a. Fetch Eval Scores from Langfuse

After running the test suite with real or stubbed LLM responses, retrieve the Eval scores from Langfuse:

```bash
# Option A: Langfuse CLI (if available)
[ENV_EXEC] langfuse eval run --dataset EVAL-NNN --prompt wiki-synthesis-v1

# Option B: Python evaluation script
[ENV_EXEC] python tests/evals/run_evals.py --rubric docs/specs/EVAL-NNN-*.md
```

The evaluation script must:
1. Load the golden dataset from `tests/evals/datasets/EVAL-NNN.jsonl`.
2. Call the LLM adapter (or fetch logged traces from Langfuse) for each input.
3. Apply the Eval judge (LLM-as-judge / embedding / rule-based) per rubric dimension.
4. Compute the numeric score for each dimension.
5. Compare against the threshold defined in the rubric.
6. **Fail the pipeline (exit code 1) if any blocking dimension falls below threshold.**

#### 4b. Eval Score Verification Table

For each dimension in the Eval Rubric, verify:

| Dimension | Threshold (pass) | Threshold (block) | Action on Block |
|-----------|------------------|--------------------|-----------------|
| `faithfulness` | ≥ 0.80 | < 0.65 | Pipeline FAILED |
| `relevance` | ≥ 0.75 | < 0.60 | Pipeline FAILED |
| `hallucination` | ≤ 0.10 | > 0.20 | Pipeline FAILED |
| `toxicity` | ≤ 0.05 | > 0.10 | Pipeline FAILED |

> [!NOTE]
> Scores between the pass and block thresholds (e.g. `0.65 ≤ faithfulness < 0.80`) are
> treated as **WARNING** — log to Langfuse with a `warning` severity tag, but do not
> block the pipeline. This mirrors the mutation testing "< 5% infrastructure survivors"
> tolerance zone.

#### 4c. Blocking Failure Resolution

If an Eval dimension fails (score below the blocking threshold):

1. **Inspect the Langfuse trace** for the failing generation: check the raw prompt, response, and latency.
2. **Root cause categories**:
   - **Prompt quality**: Update the prompt in the Langfuse Prompt Registry (bump `prompt_version`). Re-run Surgery step 4.
   - **Schema constraint**: The Pydantic model may be too loose — tighten validation in the domain Value Object. Re-run Surgery steps 4–5.
   - **Model capability**: The model may be undersized for the task — update `OLLAMA_MODEL` in settings and re-test.
   - **Golden dataset gap**: The test input may be outside the model's effective capability range — add an adversarial example and document in the rubric.
3. **Re-run the full quality gate** after remediation: `[MUTATION_EXEC]` + `[EVAL_EXEC]`.
4. The implementation is **not complete** until both mutation survivors = 0 AND Eval gate passes.

---

## 3. Decision Checklist

- [ ] Have I executed the mutation suite (`[ENV_EXEC] [MUTATION_EXEC]`) on the new code?
- [ ] Are there 0 survived mutants in the Domain and Application layers?
- [ ] If mutation tools are missing, did I achieve at least 95% line/branch coverage?
- [ ] Have I resolved all survived mutants or uncovered paths?
- [ ] Does the codebase pass static type verification (`[ENV_EXEC] [TYPE_EXEC]`) with zero errors?
- [ ] Does the linter and formatter (`[ENV_EXEC] [LINT_EXEC]`) run clean?
- [ ] **LLM Eval Gate** (mandatory for AI/LLM pipelines):
  - [ ] Have I read the Eval Rubric from `docs/specs/EVAL-NNN-*.md`?
  - [ ] Have I run `[EVAL_EXEC]` against the golden dataset?
  - [ ] Do all blocking dimensions pass (score ≥ threshold)?
  - [ ] Are warning-zone dimensions logged in Langfuse with `warning` severity?
  - [ ] If any dimension failed, has the root cause been identified and remediated (prompt update / schema tightening / model upgrade)?
  - [ ] Has the full quality gate been re-run after remediation?
- [ ] Are all quality targets met before declaring the implementation complete?
