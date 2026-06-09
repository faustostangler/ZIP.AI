# ADR Lifecycle Guide — Governance, States, and Conflict Resolution

This document defines the formal lifecycle of Architectural Decision Records (ADRs)
in the Stangler ecosystem. It governs how ADRs evolve, how metadata is consumed by
the AI agent, and how governance impasses are resolved.

---

## 1. ADR State Machine

Every ADR has a `Status` field that follows a strict state machine. Only the
transitions listed below are valid.

```
                          ┌─────────────────────┐
                          │      Proposed        │
                          └──────────┬───────────┘
                                     │
                           Lead Architect approval
                                     │
                                     ▼
                          ┌─────────────────────┐
                    ┌─────│      Accepted        │─────┐
                    │     └──────────┬───────────┘     │
                    │                │                  │
           New ADR replaces    Amendment needed    Becomes obsolete
                    │                │                  │
                    ▼                ▼                  ▼
          ┌─────────────┐   ┌──────────────┐   ┌──────────────┐
          │ Superseded   │   │   Amended    │   │  Deprecated  │
          │ by ADR-NNN   │   │  by ADR-NNN  │   │              │
          └─────────────┘   └──────────────┘   └──────────────┘
```

### State Definitions

| State | Meaning | Who Transitions |
|-------|---------|-----------------|
| **Proposed** | Initial state. The ADR has been drafted and is awaiting review. No implementation work may begin. | Author (developer or AI agent) |
| **Accepted** | The Lead Architect has explicitly approved the ADR. Implementation may proceed through the causal chain (Specs → Red → Green). | Lead Architect only |
| **Superseded by ADR-NNN** | A newer ADR has been written that replaces the decision in this one. The old ADR remains as historical record. Both the old and new ADR must cross-reference each other. | Lead Architect only |
| **Amended by ADR-NNN** | A follow-up ADR modifies part of this decision without fully replacing it. The original remains valid for the parts not amended. | Lead Architect only |
| **Deprecated** | The decision is no longer relevant (e.g., the feature was removed, the bounded context was decommissioned). No new work should reference this ADR. | Lead Architect only |

### Transition Rules

1. **Proposed → Accepted**: Requires explicit "APPROVED" from the Lead Architect.
2. **Accepted → Superseded**: A new ADR must exist first. The new ADR's `Context`
   section must reference the old ADR and explain why supersession is necessary.
3. **Accepted → Amended**: A follow-up ADR must exist. It must clearly scope which
   specific parts of the original are modified.
4. **Accepted → Deprecated**: Requires explicit justification in the deprecation
   commit message. The ADR file is not deleted — it receives a `Deprecated` status
   header and a rationale section.
5. **No backward transitions**: A `Deprecated` or `Superseded` ADR cannot return
   to `Accepted`. If the decision needs to be revisited, a new ADR must be created.

---

## 2. Metadata Consumption Protocol

When the AI agent executes the Prompt-Chaining rule (reading the predecessor
artifact before starting a new phase), it must parse and respect the following
header fields in every ADR:

### Mandatory Header Fields

```markdown
**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-{NNN} | Amended by ADR-{NNN}
**Date:** YYYY-MM-DD
**Decision Makers:** {who participated in the decision}
**Supersedes:** ADR-{NNN} (if applicable)
**Amended by:** ADR-{NNN} (if applicable)
```

### Agent Consumption Rules

1. **Status Check**: Before deriving Specs from an ADR, verify that `Status` is
   `Accepted`. If the status is `Proposed`, `Deprecated`, or `Superseded`, halt
   and notify the Lead Architect.

2. **Supersession Chain**: If the ADR is marked `Superseded by ADR-NNN`, the agent
   must follow the chain to the latest active ADR and derive work from that one
   instead. Never derive implementation from a superseded ADR.

3. **Amendment Scope**: If the ADR is marked `Amended by ADR-NNN`, the agent must
   read both the original and the amendment. The amendment takes precedence for the
   specific sections it modifies; the original remains authoritative for everything
   else.

4. **Date Awareness**: The agent should note the ADR date. ADRs older than 12 months
   that have not been reviewed may warrant a proactive suggestion to the Lead
   Architect to confirm the decision is still valid.

---

## 3. Governance Neutrality Directive

> **The agent is a strict consumer and executor of the current ADR repository state.
> It delegates political evolution and conflict resolution entirely to the human
> development team's consensus.**

### Conflict Detection Protocol

The agent may detect governance inconsistencies during its Prompt-Chaining reads.
Common conflicts include:

| Conflict Type | Example | Agent Behavior |
|---------------|---------|----------------|
| **Contradictory Accepted ADRs** | ADR-005 says "use Redis for caching"; ADR-012 says "use Memcached for caching" — both are `Accepted` | **Halt at Phase 1.** Emit a governance inconsistency alert to the Lead Architect. Do not attempt resolution. |
| **Circular Supersession** | ADR-003 superseded by ADR-007, which is superseded by ADR-003 | **Halt at Phase 1.** Report the circular reference. |
| **Orphaned Amendment** | ADR-010 is `Amended by ADR-015`, but ADR-015 does not exist or is `Deprecated` | **Halt at Phase 1.** Report the broken reference. |
| **Stale Accepted ADR** | ADR with `Accepted` status and no review in 18+ months, referenced by new work | **Warn (non-blocking).** Suggest a review cycle to the Lead Architect. |

### Non-Negotiable Neutrality Rules

1. The agent **never** resolves architectural disagreements between ADRs on its own.
2. The agent **never** changes an ADR's `Status` field — that is a human-only action.
3. The agent **never** deprecates, supersedes, or amends an ADR without explicit
   Lead Architect instruction.
4. When a conflict is detected, the agent's default behavior is to **interrupt the
   execution cycle at Phase 1 (ADR)** and request explicit clarification, emitting
   a structured alert:

```
⚠️ GOVERNANCE INCONSISTENCY DETECTED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Conflicting ADRs: ADR-{NNN} vs ADR-{NNN}
Conflict type: {Contradictory | Circular | Orphaned | Stale}
Description: {brief explanation}

ACTION REQUIRED: Lead Architect must resolve this conflict before
the execution cycle can proceed past Phase 1.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## 4. ADR Review Cadence

To prevent ADR decay and governance drift, the team should adopt periodic reviews:

| Cadence | Scope | Action |
|---------|-------|--------|
| **Quarterly** | All `Accepted` ADRs older than 6 months | Confirm or flag for re-evaluation |
| **On major release** | All ADRs referenced by the release's bounded contexts | Confirm alignment with current architecture |
| **On new team member** | ADRs for the bounded contexts the new member will touch | Onboarding walkthrough of active decisions |

The agent may proactively suggest a review when it detects an ADR older than 12
months being referenced by new work, but this is a **non-blocking warning** — it
does not halt the execution cycle.

---

## 5. ADR Numbering and Filing

| Rule | Convention |
|------|-----------|
| Sequential numbering | `ADR-001`, `ADR-002`, ..., `ADR-NNN` |
| File location | `docs/adr/ADR-NNN-short-title.md` |
| Short title | Lowercase, hyphen-separated, descriptive (e.g., `adopt-redis-cache-adapter`) |
| Never reuse numbers | Even if an ADR is deprecated, its number is retired |
| Cross-references | Use explicit `Supersedes: ADR-NNN` / `Amended by: ADR-NNN` fields |

---

## 6. Fast-Track Emergency Bypass (Production Hotfixes)

To support incident response under high pressure, the upfront ADR-first constraint may be deferred. When this occurs, the retrospective ADR must follow these specific governance rules:

### Retrospective ADR Template Modifications
- **Status**: The retrospective ADR is filed as `Proposed` immediately upon incident resolution.
- **Incident Reference**: A mandatory `Incident Ref` metadata field must link to the post-mortem, incident issue, or pager ticket.
- **Root Cause & Immediate Action**: The ADR must explicitly document the root cause and the immediate code change deployed.
- **Technical Debt Mitigation Tasks**: If the hotfix was a temporary patch or workaround, the ADR must list the permanent architectural mitigation tasks as pending issues/PRs.

### Emergency ADR Lifecycle Transition
1. **Filing**: The retrospective ADR must be created within 24 hours of incident resolution.
2. **Review**: The Lead Architect reviews the retrospective ADR to determine if the hotfix is accepted as a permanent solution or if additional refactoring is required.
3. **Transition**:
   - If permanent: Transition status to `Accepted`.
   - If temporary: Transition status to `Accepted` with a mandatory linked issue to track the permanent refactoring/strangling work. Once the permanent refactoring is complete, a new standard ADR is proposed to supersede the emergency ADR.
