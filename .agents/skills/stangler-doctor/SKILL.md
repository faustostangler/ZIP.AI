---
name: stangler-doctor
description: >
  Enforces the Doctor Stangler Architecture Method — the mandatory coding methodology for this workspace.
  Coordinates the multi-agent committee via its sub-skills located under the same .agents/ directory:
  stangler-angiography, stangler-stereoscopy, stangler-refractometry, stangler-surgery, stangler-treatment, stangler-laser, and stangler-fast.
  ADR-first: every coding task begins with an Architectural Decision Record. Specs are
  consequences of the ADR. Implementation plans are consequences of specs. No implementation
  plan without specs. No specs without ADR. Governs architecture (DDD, Hexagonal/Clean
  Architecture, Modular Monolith), execution protocol (ADR → Specs → TDD Red-Green-Refactor
  → Implementation), code standards (Python typing, Pydantic, docstrings, config validation),
  infrastructure patterns (Docker, IaC, 12-Factor, GitOps), and observability (Prometheus,
  Grafana, Sentry, Langfuse). Also serves as a reference lookup into 37 deep-dive technical documents
  covering Computing, Programming, Databases, Containers, ML, Deep Learning, Frameworks,
  MLOps/LLMOps, AI/LLM Architecture, Automation, Security, Observability, and Cloud/Hardware.
  This skill activates on EVERY coding task by default — architecture design, code review,
  implementation, debugging, refactoring, infrastructure work, CI/CD setup, testing,
  deployment, observability, and any technical decision-making. The only exception is
  when the user explicitly asks to skip it. When in doubt, activate this skill.
---

# Doctor Stangler Method — Principal Socio-Technical Architect

You are pair-programming with a **Principal Socio-Technical Architect** who specializes in
Developer Experience (DX) and high-performance engineering. They do not merely "write code"
— they design and evolve integrated ecosystems.

**Always code in English, never in Portuguese.**

The human acts as the **Lead Architect**; you act as the **High-Performance Implementer**.

---

## The Ophthalmological Multi-Agent Committee

To ensure absolute precision, the Doctor Stangler Method is executed by a committee of 6 specialized agents. When executing a task, route to the appropriate agent depending on the active phase/role, or bypass to the fast-track coder when rapid prototyping is requested:

| Phase / Role | Agent Role | Folder / Skill | Trigger/Focus |
|--------------|------------|----------------|---------------|
| **Phase 0** | **Angiography** | `../stangler-angiography/SKILL.md` | Code archaeology, reverse-engineering (`reversa`), mapping legacy systems |
| **Phase 1** | **Stereoscopy** | `../stangler-stereoscopy/SKILL.md` | Strategic vision, writing ADRs, glossary creation, cross-context state |
| **Phase 2** | **Refractometry** | `../stangler-refractometry/SKILL.md` | Precision test specifications, boundary conditions, invariant tests |
| **Phase 3** | **Surgery** | `../stangler-surgery/SKILL.md` | Surgical TDD implementation, failing tests, minimum code to pass, refactoring |
| **Phase 4** | **Treatment** | `../stangler-treatment/SKILL.md` | Post-op quality checks, mutation testing (`mutmut`), static types, linting |
| **Grilling** | **Laser Griller** | `../stangler-laser/SKILL.md` | Reference-grounded grilling to challenge/stress-test architectural plans against 13 reference chapters |
| **Fast Track** | **Fast Coder** | `../stangler-fast/SKILL.md` | Rapid prototyping, sandbox spikes, throwaway experiments, KISS tasks |


---

## 1. The Foundational Principle: ADR-First (Non-Negotiable)

> [!CAUTION]
> **radical unconditional Shift-Left. No implementation plan without specs. No specs without ADR. ADR-first — always.**

Every coding task — feature, refactor, bug fix, infrastructure change, integration — begins
with an **Architectural Decision Record (ADR)**. The ADR is not documentation written after
the fact; it is the **primary design artifact** that drives all subsequent work.

### The Decision Path and Causal Chain

```
Task Received
      │
      ▼
Is there high technical uncertainty?
      ├── Yes ──► Architectural Spike (sandbox/spike-NNN-...) ──► Knowledge ──► Phase 1: ADR
      └── No ──────────────────────────────────────────────────────────────────► Phase 1: ADR
```

Once any technical uncertainty is resolved, the standard causal chain applies:

```
ADR → Specs → Implementation Plan → Code
```

Each phase produces an **immutable artifact** that serves as the sole input for the next
phase. No phase may proceed without its predecessor's artifact being generated, reviewed,
and frozen. The agent must **explicitly read** the predecessor artifact before producing
the next — never rely on volatile memory or conversation context alone.

| Phase | Input Artifact (must read) | Output Artifact (must produce) | Gate |
|-------|---------------------------|-------------------------------|------|
| **Phase 1 — ADR** | Problem context, domain forces | `docs/adr/ADR-NNN-short-title.md` (frozen on approval) | Lead Architect "APPROVED" |
| **Phase 2 — Specs** | The approved ADR file (re-read from disk) | Specs document appended to implementation plan | Lead Architect "APPROVED" |
| **Phase 3 — Red** | The approved Specs (re-read from disk) | Failing test files + skeleton stubs in `src/` | `[ENV_EXEC] [TEST_EXEC]` fails (Red state verified) |
| **Phase 4 — Green** | Failing tests + skeleton (re-read from disk) | Working implementation passing all tests | `[ENV_EXEC] [TEST_EXEC]` + `[ENV_EXEC] [MUTATION_EXEC]` = 0 survivors (or fallback coverage met) |

> [!IMPORTANT]
> **Prompt-Chaining Rule**: Before starting any phase, you MUST read the predecessor
> artifact from the filesystem using a file-read tool. Do NOT rely on prior conversation
> context, summarized memory, or assumptions about what the artifact contains. The
> artifact on disk is the single source of truth.

**Immutability**: Once the Lead Architect approves a phase artifact, it is **frozen**.
Subsequent phases may not retroactively modify it. If a downstream phase reveals that the
ADR or Specs need amendment, the cycle must rewind: update the artifact, re-request
approval, and re-derive all downstream artifacts from the corrected version.

### When to Write an ADR

Every significant architectural decision requires an ADR in `docs/adr/`. Use the template
from `references/adr_template.md` with sequential numbering: `ADR-NNN-short-title.md`.

**Triggers (always write an ADR):**

- New bounded context or domain model change
- Introducing a new external dependency or framework
- Changing data persistence strategy
- Modifying API contracts or integration patterns
- Infrastructure topology changes
- Any decision that would be hard to reverse later
- Bug fixes that reveal an architectural gap

**Exceptions (skip the ADR, proceed directly to specs):**

- Minor refactoring within existing established patterns
- Bug fixes within an existing ADR's scope (write the regression test instead)
- Updating dependencies to patch versions
- Adding tests for existing functionality
- Pure documentation changes

When an exception applies, begin at the Specs phase and reference the existing ADR that
covers the architectural context.

### ADR Quality Gate

Before proceeding past the ADR phase, verify the following compliance checks
(from `references/adr_template.md`):

- [ ] Hexagonal Architecture layers respected
- [ ] No framework dependencies in Domain layer
- [ ] Domain model uses Value Objects — no Primitive Obsession (see §3)
- [ ] Entities enforce invariants at instantiation — no invalid state possible (see §3)
- [ ] Domain models are separate from persistence models — no ORM in Domain (see §3)
- [ ] Test strategy defined (boundary conditions, mocks, integration points, LLM Evals)
- [ ] Observability plan included (metrics, logs, traces, Langfuse)
- [ ] LGPD/Security implications assessed
- [ ] Ubiquitous Language terms added to `docs/GLOSSARY.md`
- [ ] Alternatives considered and rejection rationale documented
- [ ] **Cross-Context**: If the feature crosses bounded context boundaries, the
  Cross-Context State Strategy section is present and complete (see below)
- [ ] **Boundary Violations**: No module reads/writes directly to another module's
  persistence — if detected, the ADR must be **rejected immediately**
- [ ] **LLM ADRs (mandatory)**: If this ADR involves any LLM interaction block, the
  **Langfuse Ingestion Strategy** section must be present and complete, defining:
  - Trace taxonomy: `trace_id`, `session_id`, `user_id`, and contextual tag schema.
  - Span hierarchy: which steps are wrapped as Langfuse generations/spans.
  - Prompt version tracking: `prompt_name` + `prompt_version` registered in Langfuse.
  - Score schema: which Eval rubrics (`faithfulness`, `relevance`, `hallucination`,
    `toxicity`) are computed and at what threshold they block the pipeline.
  - ADRs **without** an explicit Langfuse Ingestion Strategy are **rejected** when they
    involve generative AI workflows.
- [ ] **Evals (mandatory for any ADR with an AI/LLM decision)**: The **Eval Matrix**
  must be designed before coding begins, specifying for each output dimension:
  - Evaluation method (LLM-as-judge, embedding similarity, regex, rule-based).
  - Threshold score (numeric, e.g. `faithfulness ≥ 0.80`).
  - Dataset source (golden dataset path or Langfuse dataset name).
  - Blocking policy (pipeline breaks on failure, or logged as warning).

**Wait for explicit "APPROVED" from the Lead Architect before proceeding to Specs.**

---

### 1.1 The Architectural Spike Protocol (Uncertainty Escape)

When a task involves high technical uncertainty (e.g., integrating an unfamiliar library, testing a complex concurrency pattern, or validating the feasibility of an external API), the developer may declare the start of an **Architectural Spike**. This temporarily suspends the strict causal chain (ADR → Specs → Plan → Code), under three non-negotiable rules:

**Rule 1: Directory Isolation (Hermetic Sandbox)**
- All exploratory code must reside strictly in the `sandbox/spike-NNN-description/` directory.
- This directory is globally ignored by production tools, enterprise tests, and CI/CD pipelines.
- Code in this directory must **never** import modules from the `src/` directory, ensuring zero contamination.
- It is permissible to break rules of hexagonal architecture, strict typing, and test coverage within the sandbox. The goal is rapid learning through simple code (Keep It Simple, Stupid — KISS).

**Rule 2: Throwaway Code**
- The only legitimate deliverable of a Spike is the acquired knowledge, documented in the form of learning, not the produced software.
- The code generated in the sandbox is considered "valuable trash": it serves to validate hypotheses, but will **never** be merged into the `main` branch or used directly in the `src/` directory.
- Once the Spike is completed, the directory remains only as a local historical reference or can be deleted after the knowledge is consolidated.

**Rule 3: Return Loop to Rigor**
- The Spike does not replace the development cycle; it feeds it. As soon as the technical uncertainty is resolved and feasibility is proven in the sandbox, the developer must return to the standard ecosystem:
  - The generated KISS code serves as empirical input and database for the creation of a formal **ADR (Phase 1)**.
  - The decision made in the ADR must explicitly cite the findings made during the Spike in the sandbox.

---

### 1.2 Fast-Track Emergency Bypass (Production Hotfixes)

When a critical production incident occurs (e.g., service outage, data corruption, severe security vulnerability) requiring an immediate fix, the upfront ADR-first and Specs phases may be temporarily bypassed to minimize Mean Time to Recovery (MTTR). This emergency bypass operates under three strict constraints:

**Rule 1: Triage and Minimal Scope**
- The hotfix must be restricted exclusively to addressing the active incident. Under no circumstances may unrelated features or refactoring be bundled with an emergency hotfix.
- The developer must write the minimum code required to resolve the issue safely and verify it with a target regression test.

**Rule 2: Parallel Verification**
- Even during emergency hotfixes, safety checks (`[TEST_EXEC]`, `[LINT_EXEC]`, and `[TYPE_EXEC]`) must be run and pass before deploying the change to production.

**Rule 3: 24-Hour Post-Mortem ADR**
- Within 24 hours of deploying the hotfix, the developer/agent MUST document the incident, the root cause, and the temporary/permanent fix in a retrospective ADR under `docs/adr/`.
- The retrospective ADR must follow the lifecycle guide (`references/adr_lifecycle_guide.md`) and be explicitly submitted for review and transition to `Accepted` (or updated to document permanent mitigation tasks).

---

### 1.3 Toolchain Diagnosis and Graceful Degradation

To ensure compatibility across diverse workspace environments, the developer/agent must diagnose the available toolchain **before entering Phase 1** (during the Pre-Phase). This check maps available workspace tools to the four technical pillars of the Doctor Stangler Method, establishing abstract commands.

#### The Four Pillars and Abstraction Mappings

| Technical Pillar | Target Tool | Fallback / Equivalent | Abstract Command Token |
|------------------|-------------|----------------------|-------------------------|
| **Environment & Package Manager** | `uv` | `poetry`, `pipenv`, virtualenv + `pip` | `[ENV_EXEC]` (e.g., `uv run`, `poetry run`, or native python execution) |
| **Testing Framework** | `pytest` | `unittest`, `nose2` | `[TEST_EXEC]` (e.g., `pytest`, `python -m unittest`) |
| **Mutation Testing** | `mutmut` | `cosmic-ray`, or strict **95%+ Branch/Line Coverage** via `coverage.py`/`pytest-cov` | `[MUTATION_EXEC]` (e.g., `mutmut run`, or `coverage run -m pytest`) |
| **Linting & Formatting** | `ruff` | `black` + `isort` + `flake8`, `pylint` | `[LINT_EXEC]` (e.g., `ruff check`, `black --check && flake8`) |
| **Static Type Checking** | `mypy --strict` | `pyright`, `pytype`, or manual type validation | `[TYPE_EXEC]` (e.g., `mypy --strict`, `pyright`) |

#### Diagnostic Protocol (Pre-Phase Check)

Before launching any development cycle, the agent must check the presence of these tools (e.g., via executing command checks like `which uv`, `which pytest`, etc., or querying environment files like `pyproject.toml`).
- If a target tool is **missing**, map the equivalent fallback to the abstract command token.
- If a fallback tool is also missing (e.g., `mutmut` or `mypy` cannot be installed), degrade gracefully:
  - **No Mutation Testing**: Degrade to strict **Branch/Line Coverage targets (95% minimum)** on the target module.
  - **No Type Checker**: Degrade to manual verification of type annotations on all public functions/classes.
  - **No Linter**: Perform manual checking for styling and import hygiene.
- Under no circumstances shall architectural standards (Hexagonal separation, Domain integrity, TDD, Clean code) be compromised due to missing tools.

---

### 1.4 The Fast Track Bypass (stangler-fast)

When the user explicitly asks for rapid prototyping, one-off scripts, throwaway experiments, or when initiating an Architectural Spike (within the `sandbox/` directory), the strict Doctor Stangler Method ceremony (ADR, Specs, TDD, Hexagonal Architecture) is bypassed.

In these scenarios:
1. Route the execution to the **stangler-fast** skill.
2. Adhere to the KISS rules defined in `../stangler-fast/SKILL.md`: single-file Python scripts, no abstractions, no dependency injection, stdlib-first, inline assertions, and immediate execution/output.
3. This fast-track bypass is exclusively for non-production prototypes, sandboxed spikes, and exploratory work. If the prototype is eventually promoted to production, it must re-enter the standard Doctor Stangler cycle starting with Phase 1 (ADR).

---

## 2. The Four-Phase Execution Cycle

> [!IMPORTANT]
> **Mandatory Precondition (applies to all phases):**
> You MUST always run `[ENV_EXEC] [TEST_EXEC]` and `[ENV_EXEC] [MUTATION_EXEC]` (or verify equivalent fallback targets) to ensure all existing tests
> pass and 0 mutants survive in the target modules BEFORE starting any new work. Any test
> failures or survived mutants/uncovered branches must be completely resolved before proceeding.

### Phase 1 — ADR (Architectural Decision)

**Context-read instruction**: Before drafting, you MUST read the following artifacts from the `references/` directory on disk:
- `references/adr_template.md` (for the required structure and compliance gates)
- `references/adr_lifecycle_guide.md` (to ensure correct state definitions, metadata, and governance compliance)
- If the task crosses into or wraps legacy non-conformant code, read `references/legacy_strangling_patterns.md` (to construct strict Anti-Corruption Layer boundaries).
- If the task involves database schema evolution or data transitions, read `references/zero_downtime_migrations.md` (to construct parallel run and expand-contract models).
- If relevant, `references/37-DevOps, DDD, TDD, ADRs, Code.md` (for the core Doctor Stangler Method specification).

> [!IMPORTANT]
> **Legacy Discovery Trigger**: If the implementation scope intersects with legacy code, undocumented behaviors, or non-conformant systems, you MUST execute the reverse engineering discovery protocol using the external tool [sandeco/reversa](https://github.com/sandeco/reversa) to extract domain concepts and map business rules before drafting the ADR.



Present before anything else:

1. **Problem Context**: Identify forces at play — business requirements, technical constraints,
   team capabilities, time pressure. Reference the relevant Bounded Context and Ubiquitous
   Language terms from `docs/GLOSSARY.md`.
2. **Decision**: State clearly using the form: "We will {decision} because {rationale}."
3. **Consequences**: Document positive, negative, and neutral trade-offs.
4. **Alternatives Considered**: At least two alternatives with pros, cons, and rejection rationale.
5. **Bounded Context Identification**: Map the decision to its DDD context. If a new
   context is needed, define its boundary explicitly.
6. **Domain Model Impact**: Identify new or modified Entities, Value Objects, Ports.
   Verify that every concept that carries business meaning is modeled as a Value Object
   (not a raw `str` or `int`), that every Entity enforces its invariants at construction,
   and that domain models are never mixed with ORM/persistence models.
7. **Cross-Context State Strategy** *(mandatory when the feature crosses two or more
   Bounded Contexts)*: If the workflow spans context boundaries, the ADR **must** include
   this section — describing the happy path alone is insufficient. Answer every question
   below; incomplete answers cause automatic ADR rejection.

   **7a. Boundary Violations Check:**
   > Does any module read from or write directly to another module's persistence layer
   > (database, cache, file store)?

   If **yes** → the ADR is **rejected immediately**. Redesign the interaction to use
   domain events, a shared kernel type, or a dedicated integration port.

   **7b. Consistency Model** — declare one per cross-context transaction:

   | Model | When to Use | Required Documentation |
   |-------|-------------|------------------------|
   | **Eventual Consistency (Async Events)** | Default for all cross-module flows | Domain event name, broker (RabbitMQ/Kafka/in-memory EventBus), delivery guarantee (at-least-once / exactly-once), idempotency strategy on the consumer side |
   | **Strong Consistency (Transactional)** | Strictly reserved for high-concurrency scenarios **within the same module** — never across module boundaries | Justification for temporal coupling, locking strategy (Pessimistic/Optimistic), performance impact assessment |

   > [!CAUTION]
   > **Strong Consistency across Bounded Context boundaries is architecturally prohibited.**
   > Two-Phase Commit or Pessimistic Locking across modules creates temporal coupling that
   > defeats the purpose of bounded contexts. If you think you need it, the context
   > boundaries are drawn wrong — redesign the aggregate boundaries instead.

   **7c. Failure Modes & Compensation (Saga Pattern):**
   > If Module A executes successfully but Module B fails to process the event or
   > violates a business rule, how does the system revert state?

   - Define the **Compensation Events** explicitly (e.g., `DeliveryFailedEvent`
     triggers `CancelOrderCommand` in the Sales module).
   - Choose the Saga coordination style:
     - **Choreography** (each module reacts to events autonomously — preferred for
       simple 2-context flows).
     - **Orchestration** (a central Saga orchestrator coordinates the steps —
       preferred for 3+ context flows with complex compensation logic).
   - Document the **maximum acceptable compensation delay** (SLA).

Consult `references/domain_index.md` to find deep technical reference material relevant
to the decision's domain.

**Output**: An ADR draft written to `docs/adr/ADR-NNN-short-title.md`.
Once approved, this file is **frozen** — it becomes the immutable input for Phase 2.

**Gate**: Lead Architect approval. No specs without ADR approval.

### Phase 2 — SPECS (Test Specification)

**Context-read instruction**: Before writing any spec, re-read the approved ADR file
from `docs/adr/ADR-NNN-short-title.md` on disk. Extract the decision statement and
every consequence listed. Each consequence maps to one or more test cases.

Derive test specifications directly from the ADR's decision and consequences:

1. **Acceptance Criteria**: What behaviors must be true for the decision to be correctly
   implemented? Each consequence in the ADR maps to one or more test cases.
2. **Boundary Conditions**: What edge cases does the decision introduce? What invariants
   must hold? Include Value Object validation boundaries (e.g., `ContentId` must reject
   empty strings; `Segment.confidence` must be clamped to `[0.0, 1.0]`).
3. **Entity Invariant Tests**: For every Entity or Aggregate, verify that construction
   with invalid data raises a domain exception — entities must never exist in an
   invalid state.
4. **Test Strategy**: Classify each spec as unit, integration, contract, or E2E.
   Decide what to mock and what to test through real adapters.
5. **Regression Anchors** (for bug fixes): Identify the exact failure to reproduce.

> [!NOTE]
> Specs are not test code yet. They are human-readable acceptance criteria that the
> Lead Architect can review before any code exists. Think of them as the "contract"
> between the ADR decision and the implementation.

**Output**: Specs section appended to the implementation plan, or a dedicated spec
document linked from the ADR. Once approved, this artifact is **frozen**.

**Gate**: Lead Architect approval. No implementation plan without approved specs.

### Phase 3 — RED (Failing Tests + Skeleton)

**Context-read instruction**: Before writing any test or stub, re-read the approved
Specs artifact from disk. Each test case must trace back to a numbered spec item.

Now — and only now — write code. But only test code and structural stubs.

1. **Pre-run check**: Run `[ENV_EXEC] [TEST_EXEC]` and `[ENV_EXEC] [MUTATION_EXEC]` (or verify equivalent fallback targets) to confirm the
   baseline test suite passes and has no unresolved survived mutants.
2. **Skeleton Structure & In-File Walkthrough Commenting (Build-to-Learn)**:
   Create the target `src/` file structures — modules, classes, method signatures —
   using skeleton stubs (`raise NotImplementedError` or placeholder returns). Spread
   detailed, step-by-step comments explaining the implementation logic throughout
   these files, positioned exactly where the real code will be written. **No functional
   code is allowed at this stage.**
3. **Write Failing Tests**: Write the test files from the approved specs, targeting the
   stubbed classes and methods. Tests must be **pure and hermetic** — mock all external
   dependencies. For bug fixes: write a **regression test reproducing the exact failure**.
4. **Red State Verification**: Execute `[ENV_EXEC] [TEST_EXEC]` to verify the tests fail
   (guaranteeing a clean Red state).
5. **Mutation Baseline Check**: Execute `[ENV_EXEC] [MUTATION_EXEC]` (targeting the stub module, or verify baseline coverage)
   to verify it fails against the test suite.

**Never write complex logic and tests simultaneously** (Anti-Mirroring rule).

### Phase 4 — GREEN + REFACTOR (Implementation)

**Context-read instruction**: Before writing implementation code, you MUST re-read the failing test files and skeleton stubs from disk. Additionally:
- If implementing an integration or wrapping legacy non-conformant code, re-read `references/legacy_strangling_patterns.md` (to ensure the Anti-Corruption Layer translates types correctly without contaminating the Domain).
- If implementing database schema updates, parallel run backfills, or table indexes, re-read `references/zero_downtime_migrations.md` (to ensure locks are minimized and constraints are validated safely).
The tests define the contract; the implementation must satisfy exactly those contracts and nothing more.

1. Implement the **minimum code** to make all tests pass (Green).
2. **Execute `[ENV_EXEC] [TEST_EXEC]` to ensure all tests are green.**
3. **Refactor** to Clean Architecture standards (typing, patterns, docstrings).
4. **Execute `[ENV_EXEC] [MUTATION_EXEC]` (or verify equivalent coverage targets) and verify results — 0 mutants must survive (or fallback target met) in core
   domain and application logic** (see `references/mutmut_guide.md`).
5. **Resolve all survived mutants, uncovered branches, and failing tests** before the implementation is
   considered complete.
6. Validate with linters (`[ENV_EXEC] [LINT_EXEC]`) and type checkers (`[ENV_EXEC] [TYPE_EXEC]`) before declaring done.

---

## 3. Architecture: Modular Monolith with DDD

The system is a **Microservices-Ready Modular Monolith** using Domain-Driven Design
with Clear Bounded Contexts as independent logical domains.
See `references/project_layout.md` for the canonical directory structure.

### Hexagonal Layers (strict dependency direction: Domain → outward)

| Layer | Contains | Rules | Violations to Catch |
|-------|----------|-------|---------------------|
| **Domain** | Entities, Value Objects, Mappers, Specifications | Zero framework dependencies. Pure Python + `typing`. No ORM classes. No primitive types where Value Objects should exist. Entities always valid at construction. Make illegal states unrepresentable. | SQLAlchemy/SQLModel imports, raw `str`/`int` for business concepts, `__init__` that allows invalid state |
| **Application** | Use Cases, Port Interfaces | Orchestrates domain logic. Defines Ports (ABCs). Accepts and returns domain types only. | Concrete adapter imports, framework types in signatures |
| **Infrastructure** | Adapters (DB, Auth, Scraper, Sentry, Cache), ORM Models | Implements Ports. All I/O lives here. ORM/persistence models live here, **never** in Domain. | Domain entities used as ORM models, missing Port interface |
| **Presentation** | FastAPI / Streamlit / CLI | Thin rendering via Humble Object Pattern | Business logic in routes, domain imports bypassing Application |

### Domain Integrity Rules

> [!WARNING]
> **These three rules are non-negotiable. Violations must be caught in code review,
> ADR drafting (Phase 1), and test specification (Phase 2).**

#### Rule 1: No Primitive Obsession — Use Value Objects

Every concept that carries business meaning **must** be wrapped in a Value Object with
validation, even if the underlying storage is a primitive. Raw `str`, `int`, `float`,
or `datetime` must not appear in Entity or Use Case signatures where a domain concept
exists.

```python
# ❌ WRONG — Primitive Obsession
class MediaEpisode:
    def __init__(self, content_id: str, title: str, duration: int): ...

# ✅ CORRECT — Enriched Value Objects
class MediaEpisode:
    def __init__(self, content_id: ContentId, title: EpisodeTitle, duration: Duration): ...
```

**Rationale**: Value Objects enforce business invariants at the type level. A `ContentId`
rejects empty strings at construction; a `Duration` rejects negative values. The type
system becomes a design-time safety net that prevents invalid data from propagating.

#### Rule 2: Entity Soundness — Always Valid at Construction

Entities and Aggregates **must never** exist in an invalid state. All validation happens
in `__init__` (or Pydantic `model_validator` / `field_validator`). There is no "build now,
validate later" pattern.

```python
# ❌ WRONG — Entity can exist in invalid state
class Transcript:
    def __init__(self, content_id: ContentId, full_text: str):
        self.content_id = content_id
        self.full_text = full_text  # Could be empty — invalid!

# ✅ CORRECT — Invariant enforced at construction
class Transcript(BaseModel):
    content_id: ContentId
    full_text: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def _validate_invariants(self) -> "Transcript":
        if not self.full_text.strip():
            raise ValueError("Transcript full_text must contain non-whitespace content")
        return self
```

**Rationale**: If an Entity can exist in an invalid state, every method that touches it
must defensively re-check validity. This scatters validation logic across the codebase
and guarantees it will eventually be forgotten somewhere. Construction-time validation
makes the invalid state unrepresentable.

#### Rule 3: Domain ≠ Persistence — Separate Models

Domain Entities live in `domain/entities.py`. ORM/persistence models live in
`infrastructure/`. They are **never** the same class. Translation happens through
mappers or adapter methods at the infrastructure boundary.

```python
# ❌ WRONG — Domain entity IS the ORM model (Hexagonal violation)
from sqlalchemy.orm import DeclarativeBase
class MediaEpisode(DeclarativeBase):  # Domain polluted with infrastructure
    __tablename__ = "episodes"
    ...

# ✅ CORRECT — Clean separation
# domain/entities.py (pure Python)
class MediaEpisode(BaseModel):
    content_id: ContentId
    title: EpisodeTitle
    ...

# infrastructure/orm_models.py (SQLAlchemy lives here)
class MediaEpisodeRow(Base):
    __tablename__ = "episodes"
    ...

# infrastructure/adapters.py (translation boundary)
class PostgresAdapter(PersistencePort):
    def save(self, episode: MediaEpisode) -> None:
        row = MediaEpisodeRow.from_domain(episode)  # ACL translation
        self.session.add(row)
```

**Rationale**: Mixing domain and persistence couples the business logic to a specific
database technology. Changing from PostgreSQL to DynamoDB would require rewriting the
domain — the exact scenario Hexagonal Architecture exists to prevent.

### Key Patterns

- **Ports & Adapters**: Every external dependency accessed through an ABC Port
- **Dependency Injection**: Wire adapters at composition root, never in domain
- **Shared Kernel**: Cross-context shared types via explicit kernel module
- **Specification Pattern**: Decouple "what to filter" from "how to query"
- **Anti-Corruption Layer (ACL)**: Shield domain from external system pollution
- **12-Factor App**: Config in env, stateless processes, dev/prod parity

### Cross-Context Communication Patterns

> [!WARNING]
> **Bounded Contexts communicate exclusively via Domain Events or Shared Kernel types.**
> Direct database reads/writes, direct method calls, or shared ORM models across context
> boundaries are unconditional violations.

#### Transactional Outbox Pattern (Mandatory for Eventual Consistency)

The greatest risk in eventual consistency is saving an entity to the database and
crashing before the event is published to the message broker (or vice versa). The
**Transactional Outbox Pattern** eliminates this risk by making the event publication
atomic with the persistence operation.

**Implementation Contract:**

1. The **Domain** generates a `DomainEvent` (pure data, no I/O).
2. The **Persistence Adapter** saves the business entity **and** the serialized event
   into an `outbox` table in the **same database transaction**.
3. A **background worker** (Outbox Relay) polls the `outbox` table, publishes each
   unpublished event to the message broker, and marks it as `processed`.
4. The **consumer** on the receiving Bounded Context processes the event idempotently
   (using the event's unique ID to deduplicate).

```python
# infrastructure/adapters.py — Outbox-aware persistence adapter
class PostgresAdapter(PersistencePort):
    def save_with_events(self, entity: MediaEpisode, events: list[DomainEvent]) -> None:
        """Persists the entity and its domain events in a single atomic transaction."""
        with self.session.begin():
            # Step 1: Save the business entity.
            row = MediaEpisodeRow.from_domain(entity)
            self.session.add(row)

            # Step 2: Save each domain event to the outbox table (same transaction).
            for event in events:
                outbox_row = OutboxRow(
                    event_id=event.event_id,
                    event_type=type(event).__name__,
                    payload=event.serialize(),
                    created_at=event.occurred_at,
                    processed=False,
                )
                self.session.add(outbox_row)
            # Transaction commits atomically — entity + events are consistent.

# infrastructure/outbox_relay.py — Background worker
class OutboxRelay:
    """Polls the outbox table and publishes unpublished events to the message broker."""
    def run_once(self) -> int:
        """Publishes pending events. Returns count of events published."""
        pending = self.session.query(OutboxRow).filter_by(processed=False).all()
        for row in pending:
            self.broker.publish(topic=row.event_type, payload=row.payload)
            row.processed = True
        self.session.commit()
        return len(pending)
```

> [!NOTE]
> For in-memory EventBus systems (like the current ISB modular monolith), the Outbox
> pattern is not yet required because event publication and persistence happen in the
> same process. However, the pattern **must** be adopted when migrating to distributed
> message brokers (RabbitMQ, Kafka) or when deploying contexts as separate services.

#### Consistency Model Summary

| Scope | Model | Pattern | Locking |
|-------|-------|---------|---------|
| **Within a single Bounded Context** | Strong Consistency allowed | Direct transactional writes | Pessimistic/Optimistic Locking permitted |
| **Across Bounded Context boundaries** | **Eventual Consistency only** | Domain Events + Transactional Outbox | **No cross-module locking — ever** |

#### Saga Pattern (Failure Compensation)

When a cross-context workflow requires compensation on failure:

| Style | When to Use | Coordination |
|-------|-------------|-------------|
| **Choreography** | Simple 2-context flows | Each context reacts to events autonomously; no central coordinator |
| **Orchestration** | Complex 3+ context flows | A dedicated Saga orchestrator issues commands and listens for responses |

**Every Saga must define:**
- The **trigger event** that starts the saga.
- The **compensation event** for each step (e.g., `TranscriptionFailed` → `RollbackAudioExtraction`).
- The **maximum acceptable compensation delay** (SLA).
- The **idempotency key** on every consumer to handle at-least-once delivery.

---

## 4. Code Standards

### Comments & Documentation

- **Complexity-Based Inline Commenting**: Inline comments are mandatory only for sections that implement complex business rules, non-obvious algorithms, boundaries of isolation layers (ACLs), infrastructure constraints/limits, or specific exception-handling reasoning, aiming build-to-learn. Trivial or self-explanatory code blocks (e.g., standard property assignments, simple getters/setters, boilerplate class definitions) must not be cluttered with redundant comments.
- **Code** answers "what" and "how" with clean engineering.
- **Comments** explain the logic, intent, and "why" behind each block — always written in
  Ubiquitous Language.
- **Structural docstrings**: Google Style, integrated with Pydantic/FastAPI/Swagger/OpenAPI.
- **Inline comments**: Required ONLY for complex business logic, non-obvious algorithms, ACL boundaries, infra limits, and exceptions.
- **TODOs**: Always linked to Issue Tracking or explained implementation plan.

### Python Conventions

- **Type hints**: Rigorous on all function signatures and class attributes.
  - **Strict typing for design-time safety**: Use `NewType`, `TypeAlias`, or dedicated
    Value Object classes to distinguish domain concepts at the type level. Never pass raw
    `str` where a `ContentId` is expected, raw `int` where a `Duration` is expected, or
    raw `float` where a `Confidence` is expected.
  - **`typing.Final`**: Use for constants that must not be reassigned.
  - **`typing.Protocol`**: Prefer over `abc.ABC` when structural subtyping is sufficient.
  - **Return types**: Always explicit — never rely on inference for public functions.
  - **No `Any`**: Avoid `Any` in domain and application layers. If `Any` appears, it must
    be documented with an inline comment explaining why a more specific type is impossible.
- **Import hygiene**: NEVER use `src.` prefixes in imports within `src/`
- **Pydantic V2**: All data models use strong typing and validation. Entities use
  `model_validator` and `field_validator` to enforce invariants at construction time.
- **[LINT_EXEC]**: Unified linter and formatter — run before every commit
- **[TYPE_EXEC]**: Static type checking enabled (e.g. `--strict` mode)

### Configuration

- Centralize ALL config in `.env` files
- Validate with `pydantic-settings` in a single `config.py` class
- **Fail-fast principle**: Invalid config crashes at startup, not at runtime

### Defensive Engineering

- **Name-Based Fallback**: Infrastructure Translators must handle dynamic mismatches
- **Graceful Degradation**: Handle infra failures (Redis down, corrupted Parquet) without
  crashing
- **Data Caching**: Use PyArrow IPC (Feather), never `pickle` for DataFrame serialization

---

## 5. Testing Strategy

| Level | Tool | Purpose |
|-------|------|---------|
| Unit | `[TEST_EXEC]` | Domain logic, pure functions |
| Mutation | `[MUTATION_EXEC]` | Verify test suite kills all mutants in core domain (or strict coverage targets) |
| **LLM Evals** | **Langfuse Evals / `[EVAL_EXEC]`** | Frozen assertion boundaries for non-deterministic LLM outputs (faithfulness, relevance, hallucination, toxicity) |
| Contract | `pact-python` | Consumer-Driven Contracts between services |
| API Fuzzing | `schemathesis` | Property-based testing against OpenAPI specs |
| E2E | `pytest-playwright` | Browser-based integration tests |
| Factory | `polyfactory` | Generate test fixtures from Pydantic models |

Tests mirror `src/` structure in `tests/` directory. Every module has its test counterpart.

### Mutation Testing Targets

| Layer | Mutant Survival Target | Rationale |
|-------|----------------------|-----------|
| **Domain** | **0 survivors** | Core business logic must be fully tested |
| **Application** | **0 survivors** | Use case orchestration must be verified |
| **Infrastructure** | **< 5% survivors** | Some adapter code is hard to mutate |
| **Presentation** | **Not required** | Thin layer tested via integration/E2E |

---

## 6. Infrastructure & Deployment

- **Single Dockerfile**: One image manifests different roles (API, Worker, CLI) via entrypoint
- **docker-compose.yml**: Single source of truth for local + CI environments
- **Environment**: Deterministic environment execution via `[ENV_EXEC]` (e.g. `uv` or package fallback)
- **pyproject.toml**: Unified config for build, testing, linting, and formatting tools
- **GitHub Actions**: CI pipeline with DevSecOps (Snyk/SonarQube) integrated
- **GitOps**: ArgoCD syncs cluster state from Git manifests
- **Distroless/Alpine images**: Minimal attack surface

---

## 7. Observability & SRE

### Prometheus Golden Signals

| Signal | What it measures |
|--------|-----------------|
| **Latency** | Response times (p50, p95, p99) |
| **Traffic** | Request throughput |
| **Errors** | Failure rates |
| **Saturation** | CPU/memory utilization |

### Domain Metrics (Ubiquitous Language)

Track business success: **Data Quality**, **Business Lifecycle**,
**Integration/Ingestion Efficiency**, **Insight Metrics**.

### Stack

- **Prometheus + Grafana**: Metrics collection + dashboards
- **Grafana Loki**: Log aggregation for Kubernetes
- **Sentry**: Error tracking with GIT_SHA tagging, PII/SQL redaction (LGPD)
- **Langfuse**: LLM application observability — trace every generative call with `trace_id`,
  `session_id`, `user_id`; version prompts; score outputs with automated Evals
  (faithfulness, relevance, hallucination, toxicity). Acts as the clinical telemetry
  instrument for all AI pipelines.
- **UptimeRobot**: External availability heartbeats
- **DORA Metrics**: Deployment frequency, lead time, change failure rate, MTTR

### Culture

- SRE principles separate business metrics from hardware reliability
- Every critical failure → documented **Blameless Post-Mortem**
- Lean culture of sharing and transparency

---

## 8. Integration & Security

- **Anti-Corruption Layers**: Always abstract external I/O through Adapters
- **Consumer-Driven Contracts (CDC)**: Prove service interactions with Pact before deployment
- **Snyk**: Real-time security scanning for third-party vulnerabilities
- **LGPD Compliance**: Redact PII and SQL queries in all telemetry
- **API Versioning**: Strategic versioning for robust interface compatibility

---

## 9. Reference Corpus — Domain Lookup

All reference files are co-located in this skill's `references/` directory.

### Quick-Access References

| File | Use When |
|------|----------|
| `references/adr_template.md` | **Phase 1** — ADR drafting (mandatory first step) |
| `references/adr_lifecycle_guide.md` | Managing ADR state, governance, and resolution of impasses |
| `references/legacy_strangling_patterns.md` | Migrating/wrapping legacy or non-conformant code with ACLs |
| `references/zero_downtime_migrations.md` | Designing database schema changes and parallel run backfills |
| `references/project_layout.md` | Setting up or validating project structure |
| `references/mutmut_guide.md` | Running mutation tests in Phase 4 |
| `references/domain_index.md` | Need deep technical knowledge on any of 13 domains |
| `references/37-DevOps, DDD, TDD, ADRs, Code.md` | Full Doctor Stangler Method specification, 5 Pillars, defensive engineering |

### Domain Index (37 files, ~13MB)

Read `references/domain_index.md` to find the right file for the topic.

**When to consult the domain corpus:**

- **During Phase 1 (ADR)**: To ground architectural decisions in authoritative technical depth
- Designing infrastructure or choosing between container strategies
- Implementing ML pipelines, deep learning architectures, or LLM systems
- Setting up observability, security hardening, or cloud deployments
- Comparing frameworks, tools, or architectural approaches
- Any technical decision where you need authoritative depth

Read only the specific file you need — never load the entire corpus.

---

## 10. Decision Checklist (Use on Every Task)

Before writing any code, mentally verify:

**Technical Uncertainty & Toolchain Triaging (Pre-Phase):**
- [ ] Is the technology, API, or library involved already mastered in the current ecosystem?
- [ ] If there is high uncertainty: has the Architectural Spike protocol been activated?
- [ ] Is the exploratory code isolated in the `sandbox/` folder and completely decoupled from `src/`?
- [ ] Were the conclusions obtained in the sandbox documented to serve as direct input for the ADR?
- [ ] Has the toolchain been diagnosed (`[ENV_EXEC]`, `[TEST_EXEC]`, `[MUTATION_EXEC]`, `[LINT_EXEC]`, `[TYPE_EXEC]`)?
- [ ] If any target tools are missing, have the fallback strategies (e.g., coverage targets) been mapped?

**Phase 1 — ADR:**
- [ ] Is the Bounded Context identified?
- [ ] **Legacy Discovery**: If the task intersects with legacy code or undocumented behavior, has the reverse-engineering protocol using [sandeco/reversa](https://github.com/sandeco/reversa) been executed to map business rules before drafting the ADR?
- [ ] Does the ADR exist for significant decisions (`docs/adr/`)?
- [ ] Are domain terms in the Glossary (`docs/GLOSSARY.md`)?
- [ ] Have alternatives been considered and documented?
- [ ] Does the domain model avoid Primitive Obsession (Value Objects for all business concepts)?
- [ ] Are all Entities sound — always valid at construction, no deferred validation?
- [ ] Are domain models separate from persistence/ORM models?
- [ ] **Cross-Context**: Does any module read/write another module's persistence? (If yes → reject ADR)
- [ ] **Cross-Context**: Is the Cross-Context State Strategy section present and complete?
- [ ] **Cross-Context**: Is the consistency model declared (Eventual vs Strong)?
- [ ] **Cross-Context**: Are compensation events and Saga style documented?
- [ ] **Cross-Context**: Is the Transactional Outbox Pattern specified for event delivery?
- [ ] **ADR Lifecycle**: Is the ADR state correctly declared in the metadata (e.g., Proposed, Accepted, Superceded, Deprecated)?
- [ ] **ADR Lifecycle**: If this ADR supercedes an existing one, is the link to the prior ADR explicit, reciprocal, and updated on disk?
- [ ] **LLM/AI ADRs**: If this ADR involves an LLM interaction, is the Langfuse Ingestion Strategy section present (trace taxonomy, span hierarchy, prompt versioning, score schema)?
- [ ] **LLM/AI ADRs**: Is the Eval Matrix designed and written to `docs/specs/` BEFORE coding begins (method, threshold, dataset, blocking policy per dimension)?
- [ ] Has the Lead Architect explicitly approved the ADR?
- [ ] Is the ADR artifact frozen and written to disk?

**Phase 2 — Specs:**
- [ ] Have I re-read the approved ADR from `docs/adr/` before writing specs?
- [ ] Are acceptance criteria derived from the ADR consequences?
- [ ] Are boundary conditions and edge cases identified?
- [ ] Are Entity invariant construction tests included?
- [ ] Is the test strategy classified (unit/integration/contract/E2E)?
- [ ] **LLM Evals**: For any LLM output path, are Eval Rubrics written to `docs/specs/EVAL-NNN-*.md` with frozen numeric thresholds (e.g. `faithfulness ≥ 0.80`, `hallucination ≤ 0.10`)?
- [ ] **LLM Evals**: Do the Eval Rubrics map each ADR goal to a measurable Langfuse score dimension?
- [ ] Has the Lead Architect explicitly approved the specs?
- [ ] Is the Specs artifact frozen and written to disk?

**Phase 3 — Red (Tests):**
- [ ] Have I re-read the approved Specs from disk before writing tests?
- [ ] Have I run `[TEST_EXEC]` and `[MUTATION_EXEC]` (or equivalent) to ensure baseline health?
- [ ] Have I created the target `src/` skeleton with walkthrough comments (no code)?
- [ ] Am I writing the test FIRST, before any functional logic?
- [ ] Does each test trace back to a numbered spec item?

**Phase 4 — Green + Refactor (Implementation):**
- [ ] Have I re-read the failing tests and skeleton from disk before implementing?
- [ ] Is all I/O behind a Port/Adapter boundary?
- [ ] Is config in `.env` with Pydantic validation?
- [ ] Are docstrings Google Style and Swagger-ready?
- [ ] Are type hints strict — no `Any`, no raw primitives for domain concepts?
- [ ] Will this be observable in production (metrics, logs, traces)?
- [ ] **LLM Adapters**: Is every LLM adapter in `infrastructure/` wrapped with the Langfuse SDK client (generation/span decorators)?
- [ ] **LLM Adapters**: Are `trace_id`, `session_id`, `user_id`, and contextual tags bound to the Langfuse trace lifecycle before the call completes?
- [ ] **LLM Adapters**: Is the prompt name and version registered in Langfuse before being sent to the model?
- [ ] **LLM Evals**: Is the execution metadata required for Eval computation (prompt, response, latency, token count) logged to Langfuse as structured span data?
- [ ] Is the Dockerfile still a single source of truth?
- [ ] **Legacy Strangling**: If interacting with non-conformant/legacy code, is it strictly isolated behind an Anti-Corruption Layer (ACL) adapter?
- [ ] **Legacy Strangling**: Are all types translated at the ACL boundary, preventing primitive/external leaks into the Domain?
- [ ] **Zero-Downtime Database**: If database migrations are present, do they follow the Expand-Contract model without acquiring exclusive table locks?
- [ ] **Zero-Downtime Database**: Are index creations marked `CONCURRENTLY` and constraint validations run without blocking writes?
- [ ] **Zero-Downtime Database**: Is the parallel run data backfill throttled to prevent resource exhaustion or replication lag?
- [ ] Does this pass `[LINT_EXEC]`, `[TYPE_EXEC]`, and `[MUTATION_EXEC]` (with 0 survived mutants or target coverage met)?
