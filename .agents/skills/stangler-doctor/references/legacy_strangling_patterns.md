# Legacy Strangling Patterns — ACL Isolation for Non-Conformant Code

This document establishes the engineering protocols for migrating legacy code into
the Stangler ecosystem without contaminating the clean Domain. It defines the
Anti-Corruption Layer (ACL) construction directives, the reverse-engineering
discovery protocol, and the Strangler Fig progression model.

---

## 1. The Cognitive Isolation Principle

> **Legacy code artifacts — whether discovered through manual reading, automated
> reverse-engineering, or runtime observation — serve strictly as cognitive input
> for ADR elaboration (Phase 1). They must never be copied, adapted, or directly
> referenced in the clean Domain or Application layers.**

The boundary between the legacy world and the new Domain is absolute. Knowledge
flows inward (legacy → understanding → ADR); code never does.

```
┌─────────────────────────────────────────────────────────────┐
│                    LEGACY WORLD                             │
│  (spaghetti code, implicit contracts, undocumented rules)   │
└────────────────────────┬────────────────────────────────────┘
                         │
              Reverse-Engineering Discovery
              (cognitive extraction only)
                         │
                         ▼
              ┌─────────────────────┐
              │    ADR (Phase 1)    │
              │  Documents the      │
              │  discovered rules   │
              │  as formal domain   │
              │  decisions          │
              └──────────┬──────────┘
                         │
                Stangler Causal Chain
              (Specs → Red → Green)
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLEAN DOMAIN                             │
│  (Value Objects, Entities, Ports — no legacy contamination) │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Code Archaeology and Discovery

Before designing the Anti-Corruption Layer (ACL), the migration engineering framework recommends utilizing the skill/tool [sandeco/reversa](https://github.com/sandeco/reversa) to perform reverse engineering on the legacy codebase. The output of this tool MUST be utilized as cognitive knowledge input (Knowledge) to isolate the actual business rules from the accidental behavior of the legacy system.

---

## 3. Legacy Ingestion Protocol

When a development task intercepts behavior or logic residing in non-conformant
legacy code, the following protocol activates:

### Step 1: Legacy Boundary Identification

Identify the exact boundary of the legacy system being touched:

| Question | Purpose |
|----------|---------|
| What external system or module contains the legacy logic? | Scoping the ACL perimeter |
| Is this legacy code under our control or third-party? | Determines write access and refactoring latitude |
| What implicit contracts exist (undocumented APIs, side effects, shared state)? | Mapping the hidden coupling |
| What data formats does the legacy system produce/consume? | Defining the translation layer |

### Step 2: Discovery Execution

The recommended approach for understanding legacy logic follows this priority order:

1. **Runtime Observation**: Instrument the legacy system with logging/tracing to
   observe actual behavior under production-like conditions.
2. **Automated Reverse-Engineering**: Use external analysis and extraction tools, primarily [sandeco/reversa](https://github.com/sandeco/reversa), to execute automated reverse engineering and extract domain rules/structures from the legacy codebase.
3. **Manual Code Reading**: As a last resort, read the legacy source directly. Take
   notes, not code.

> [!WARNING]
> The output of any discovery step is **documentation** (notes, diagrams, behavior
> observations), never executable code. If you find yourself copying functions or
> classes from the legacy codebase, you are violating the Cognitive Isolation Principle.

### Step 3: ADR Formalization

The discovered legacy behavior must be formalized as an ADR (Phase 1) that:

- Documents the **business rules** hidden in the legacy code (what the code does
  in domain terms, not how it does it mechanically).
- Identifies the **implicit contracts** the legacy system depends on.
- Proposes the **clean Domain model** that will replace the legacy behavior.
- Designs the **ACL** that will shield the new Domain during the transition period.

---

## 4. Anti-Corruption Layer (ACL) Construction Directives

The ACL is an Infrastructure-layer adapter that translates between the legacy world's
data formats, protocols, and conventions and the clean Domain's Value Objects and
Entities.

### ACL Architecture

```
┌──────────────┐     ┌──────────────────────┐     ┌──────────────────┐
│  Legacy      │     │  Anti-Corruption      │     │  Clean Domain    │
│  System      │◄───►│  Layer (ACL)          │◄───►│  Port            │
│              │     │                       │     │                  │
│  - Raw types │     │  - LegacyTranslator   │     │  - Value Objects │
│  - Implicit  │     │  - DataSanitizer      │     │  - Entities      │
│    contracts │     │  - ContractAdapter     │     │  - Domain Events │
└──────────────┘     └──────────────────────┘     └──────────────────┘
```

### Construction Rules

1. **Location**: ACLs live exclusively in the `infrastructure/` layer of the
   relevant bounded context. Never in `domain/` or `application/`.

2. **Translation Boundary**: The ACL translates legacy data formats into Domain
   Value Objects at the boundary. Raw legacy types (`dict`, untyped `str`, legacy
   ORM models) must never cross into the Domain.

3. **Defensive Sanitization**: The ACL must sanitize and validate all incoming
   legacy data before constructing Domain objects. Assume legacy data is untrusted:
   - Null/empty checks for fields the Domain requires as non-optional.
   - Type coercion for fields the legacy system stores in wrong types.
   - Business rule enforcement that the legacy system may not have applied.

4. **Failure Isolation**: ACL failures (legacy system unavailable, data corruption,
   schema drift) must be caught and translated into Domain-specific exceptions.
   Legacy stack traces, error codes, and internal details must never propagate
   beyond the ACL.

5. **Interface Stability**: The ACL implements a Domain Port (ABC). If the legacy
   system's API changes, only the ACL adapter is modified — the Port interface
   and all Domain/Application code remain untouched.

```python
# ❌ WRONG — Legacy pollution crosses into Domain
class ProcessLegacyUseCase:
    def execute(self, legacy_record: dict) -> None:
        # Domain is polluted with untyped legacy structures
        name = legacy_record.get("nm_usr", "")  # Legacy field name leaked
        ...

# ✅ CORRECT — ACL translates at the boundary
class LegacyUserACL(UserRepositoryPort):
    """Anti-Corruption Layer: translates legacy user records into Domain entities."""

    def find_by_id(self, user_id: UserId) -> User:
        raw = self._legacy_client.get_user(str(user_id))  # Legacy call
        # ACL translation: legacy dict → Domain Value Objects → Entity
        return User(
            user_id=user_id,
            name=UserName(raw.get("nm_usr", "")),        # Sanitized + wrapped
            email=EmailAddress(raw.get("ds_email", "")),  # Validated + typed
        )
```

---

## 5. Strangler Fig Progression Model

The migration from legacy to clean code follows a three-stage lifecycle inspired
by the Strangler Fig pattern (Martin Fowler). Each stage has a clear definition of
done and a gate controlled by the Lead Architect.

```
[Stage 1: Wrap] ──► [Stage 2: Replace] ──► [Stage 3: Retire]
```

### Stage 1: Wrap

**Goal**: Encapsulate the legacy system behind an ACL without modifying its internals.

| Action | Constraint |
|--------|-----------|
| Build the ACL adapter in `infrastructure/` | Must implement a Domain Port (ABC) |
| Route all new code through the ACL | No direct calls to the legacy system from Application or Domain |
| Write integration tests for the ACL | Verify translation fidelity against real legacy responses |

**Gate**: The ACL is tested, deployed, and all new features use it exclusively.

### Stage 2: Replace

**Goal**: Implement the clean Domain logic that will eventually replace the legacy
behavior.

| Action | Constraint |
|--------|-----------|
| Write the ADR for the replacement (if not already done) | Follow the full Phase 1 → 4 causal chain |
| Implement the clean Domain model, Application use cases, and new Infrastructure adapters | Must pass all mutation testing targets |
| Run both systems in parallel (legacy via ACL + clean implementation) | Verify behavioral parity through contract tests |

**Gate**: The clean implementation passes all tests and demonstrates behavioral
equivalence with the legacy system under production-like data.

### Stage 3: Retire

**Goal**: Remove the legacy dependency entirely.

| Action | Constraint |
|--------|-----------|
| Switch routing from ACL to clean adapter | Feature flag or gradual rollout recommended |
| Remove the ACL adapter code | Only after the clean path is proven in production |
| Deprecate the legacy system access | Update ADR status to reflect the completed migration |
| Archive (do not delete) legacy-related test fixtures | Historical reference for regression analysis |

**Gate**: The legacy system is no longer called by any production code path. The
ACL adapter is removed. The migration ADR is updated to `Accepted` with a
completion note.

---

## 6. Legacy Code Detection Heuristics

The agent should watch for these signals that indicate legacy code is being
encountered during a task:

| Signal | Implication |
|--------|------------|
| Imports from directories outside `src/` canonical structure | Possible legacy module dependency |
| Untyped `dict` or `Any` used as function parameters in data-carrying roles | Possible legacy data format leaking into Domain |
| Direct database queries without a Repository Port | Possible legacy persistence pattern |
| Business logic embedded in HTTP route handlers or CLI scripts | Possible legacy monolith pattern |
| Comments referencing "old system", "legacy", "deprecated", "workaround" | Explicit legacy markers |
| Functions with 100+ lines or deeply nested conditionals | Possible spaghetti code requiring strangling |

When any of these signals are detected, the agent should suggest activating the
Legacy Ingestion Protocol to the Lead Architect before proceeding with the task.
