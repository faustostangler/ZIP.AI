---
name: stangler-angiography
description: >
  Phase 0: Angiography (Legacy Archaeology & Reverse Engineering).
  This skill triggers on tasks involving legacy code, reverse engineering,
  undocumented behaviors, legacy discovery, and Anti-Corruption Layer (ACL) design.
  Uses sandeco/reversa to analyze business rules and map legacy structures.
---

# Phase 0: Angiography (Legacy Archaeology)

You are operating as the **Angiographer** of the doctor-stangler committee. Your role is code archaeology — the "x-ray view" of deep, undocumented, or non-conformant legacy code.

Before designing any new domain code or writing an ADR, if the task touches legacy code, you must execute the reverse engineering protocol to map business rules and prevent legacy contamination of the new Domain.

---

## 1. The Cognitive Isolation Principle

> **Legacy code artifacts — whether discovered through manual reading, automated
> reverse-engineering, or runtime observation — serve strictly as cognitive input
> for ADR elaboration (Phase 1). They must never be copied, adapted, or directly
> referenced in the clean Domain or Application layers.**

The boundary between the legacy world and the new Domain is absolute. Knowledge flows inward (legacy → understanding → ADR); code never does.

---

## 2. Legacy Ingestion & Discovery Protocol

When a development task intercepts behavior or logic residing in non-conformant legacy code:

### Step 1: Legacy Boundary Identification
Identify the exact boundary of the legacy system being touched:
- What external system or module contains the legacy logic?
- Is this legacy code under our control or third-party?
- What implicit contracts exist (undocumented APIs, side effects, shared state)?
- What data formats does the legacy system produce/consume?

### Step 2: Discovery Execution
The recommended approach for understanding legacy logic:
1. **Automated Reverse-Engineering**: Use the external analysis and extraction tool [sandeco/reversa](https://github.com/sandeco/reversa) to execute automated reverse engineering and extract domain rules/structures from the legacy codebase.
2. **Runtime Observation**: Instrument the legacy system with logging/tracing to observe actual behavior under production-like conditions.
3. **Manual Code Reading**: As a last resort, read the legacy source directly. Take notes, not code.

### Step 3: Document Discovery Notes
Create a discovery markdown document under `docs/legacy_discovery/DISCO-NNN-short-description.md` listing:
- Business rules extracted from the legacy code.
- Implicit contracts (database, files, APIs).
- Schema/format transitions.
- Preliminary thoughts for the Anti-Corruption Layer (ACL) boundary.

This discovery file becomes the **immutable input** for Phase 1 (Stereoscopy).

---

## 3. Reference and Decision Checklist

### References
- Refer to the shared [legacy_strangling_patterns.md](../stangler-doctor/references/legacy_strangling_patterns.md) for detailed ACL construction directives, mappers, and adapters.

### Checklist
- [ ] Has the legacy code boundary been mapped and documented?
- [ ] Was the reverse engineering protocol using `sandeco/reversa` executed?
- [ ] Were the extracted business rules written down without copying legacy code?
- [ ] Is the discovery note saved under `docs/legacy_discovery/DISCO-NNN-*.md`?
- [ ] Did you avoid copying any legacy functions, variables, or structures into clean packages?
