# ADR Format

ADRs live in `docs/adr/` and use sequential numbering: `ADR-NNN-slug.md` (e.g., `ADR-001-slug.md`, `ADR-002-slug.md`, etc.).

Create the `docs/adr/` directory lazily — only when the first ADR is needed.

## Template

```markdown
# ADR-{NNN}: {Short Title}

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-{NNN}
**Date:** YYYY-MM-DD
**Decision Makers:** {who participated in the decision}

## Context

Describe the forces at play — business requirements, technical constraints,
team capabilities, time pressure. What is the problem or opportunity?

Include relevant Bounded Context and Ubiquitous Language terms from `docs/GLOSSARY.md`.

## Decision

State the architectural decision clearly and concisely.
Use the form: "We will {decision} because {rationale}."

## Consequences

### Positive
- What becomes easier or better?
- What new capabilities does this unlock?

### Negative
- What trade-offs are we accepting?
- What becomes harder or more complex?

### Neutral
- What changes but is neither positive nor negative?

## Alternatives Considered

### Alternative A: {Name}
- **Pros:** ...
- **Cons:** ...
- **Why rejected:** ...

### Alternative B: {Name}
- **Pros:** ...
- **Cons:** ...
- **Why rejected:** ...

## Cross-Context State Strategy (Mandatory for cross-module flows)
*If transaction spans multiple contexts:*
- Boundary Violations check: (Does any module read/write another module's database? If yes, reject.)
- Consistency Model: (Eventual Consistency vs Strong Consistency)
- Failure Modes & Compensation (Saga Pattern): (Compensation events, Orchestration vs Choreography, SLA delay, idempotency keys)
- Transactional Outbox Pattern implementation: (Outbox table, Relay worker detail)

## Langfuse Ingestion Strategy (Mandatory for AI/LLM blocks)
*If decision involves generative AI calls (LLM, embeddings, reranking, agents):*
- Trace Taxonomy: (trace_id, session_id, user_id, tags)
- Span Hierarchy: (generations, spans, inputs/outputs)
- Prompt Version Tracking: (prompt_name + prompt_version registered in Langfuse)
- Score Schema & Blocking Thresholds: (faithfulness, relevance, hallucination, toxicity metrics)

## Compliance

- [ ] Hexagonal Architecture layers respected
- [ ] No framework dependencies in Domain layer
- [ ] Tests strategy defined (boundary conditions, mock boundary, evals)
- [ ] Observability plan included
- [ ] LGPD/Security implications assessed

## References

- Related ADRs: ADR-{NNN}
- Issue Tracker: #{issue-number}
- Domain reference: `references/{domain-file}.md`
```

## When to Write an ADR

All three of these must be true:

1. **Hard to reverse** — the cost of changing your mind later is meaningful
2. **Surprising without context** — a future reader will look at the code and wonder "why on earth did they do it this way?"
3. **The result of a real trade-off** — there were genuine alternatives and you picked one for specific reasons

If a decision is easy to reverse, skip it. If it's not surprising, nobody will wonder why. If there was no real alternative, there's nothing to record.

### What qualifies

- **Architectural shape.** "We're using a monorepo." "The write model is event-sourced, the read model is projected into Postgres."
- **Integration patterns between contexts.** "Ordering and Billing communicate via domain events, not synchronous HTTP."
- **Technology choices that carry lock-in.** Database, message bus, auth provider, deployment target.
- **Boundary and scope decisions.** "Customer data is owned by the Customer context; other contexts reference it by ID only."
- **Deliberate deviations from the obvious path.** "We're using manual SQL instead of an ORM because X."
- **Constraints not visible in the code.** "We can't use AWS because of compliance requirements."
- **Rejected alternatives when the rejection is non-obvious.**
