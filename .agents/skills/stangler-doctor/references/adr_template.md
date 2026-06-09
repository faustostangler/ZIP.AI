# ADR Template — Architectural Decision Record

Use this template for every significant architectural decision.
Store ADRs in `docs/adr/` with sequential numbering: `ADR-001-short-title.md`.

---

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

## Compliance

- [ ] Hexagonal Architecture layers respected
- [ ] No framework dependencies in Domain layer
- [ ] Tests strategy defined
- [ ] Observability plan included
- [ ] LGPD/Security implications assessed

## References

- Related ADRs: ADR-{NNN}
- Issue Tracker: #{issue-number}
- Domain reference: `references/{domain-file}.md`
```

---

## Naming Convention

| Pattern | Example |
|---------|---------|
| Feature | `ADR-001-adopt-chromadb-for-vector-storage.md` |
| Architecture | `ADR-002-hexagonal-layer-separation.md` |
| Integration | `ADR-003-redis-cache-adapter-pattern.md` |
| Infrastructure | `ADR-004-single-dockerfile-multi-role.md` |

## When to Write an ADR

- New bounded context or domain model change
- Introducing a new external dependency or framework
- Changing data persistence strategy
- Modifying API contracts or integration patterns
- Infrastructure topology changes
- Any decision that would be hard to reverse later

## When NOT to Write an ADR

- Minor refactoring within existing patterns
- Bug fixes that don't change architecture
- Updating dependencies to patch versions
- Adding tests for existing functionality
