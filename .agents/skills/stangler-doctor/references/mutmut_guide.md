# Mutation Testing with mutmut — Guide

Mutation testing verifies that your test suite actually catches bugs, not just
that it runs green. It works by introducing small changes ("mutants") to your
source code and checking whether your tests detect them.

**The Stangler Method requires 0 surviving mutants in core domain logic.**

---

## How It Works

1. **mutmut** modifies your source code with small mutations (e.g., `+` → `-`, `True` → `False`, `==` → `!=`)
2. For each mutation, it runs your test suite
3. If tests **fail** → mutant is **killed** ✅ (your tests caught the bug)
4. If tests **pass** → mutant **survived** ❌ (your tests missed it)

---

## Setup

### pyproject.toml Configuration

```toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest -x --tb=no -q"
dict_synonyms = "Faker"
```

### Running mutmut

```bash
# Run mutation testing on all source code
uv run mutmut run

# Run on a specific module (recommended for targeted checks)
uv run mutmut run --paths-to-mutate src/ingestion/domain/

# Run on a specific file
uv run mutmut run --paths-to-mutate src/ingestion/domain/entities.py
```

---

## Interpreting Results

### Summary Output

```
Legend for output:
🎉 Killed mutants      — Tests caught the mutation (GOOD)
⏰ Timeout              — Mutation caused infinite loop (usually GOOD)
🤔 Suspicious           — Needs manual review
🙁 Survived mutants     — Tests DID NOT catch the mutation (BAD)
🔇 Skipped              — Mutant was not testable
```

### Viewing Results

```bash
# Show overall summary
uv run mutmut results

# Show surviving mutants (the ones you need to fix)
uv run mutmut results --survived

# Show a specific mutant's diff
uv run mutmut show <mutant-id>

# Show all surviving mutants as diffs
uv run mutmut show all --survived

# Generate HTML report
uv run mutmut html
# Opens at htmlcov/mutmut.html
```

### What Each Result Means

| Result | Meaning | Action |
|--------|---------|--------|
| **Killed** | Test suite caught the mutation | None — your test is effective |
| **Timeout** | Mutation caused an infinite loop | Usually fine — test detected the issue indirectly |
| **Survived** | Tests passed despite the mutation | **Write a new test** that catches this specific case |
| **Suspicious** | Test behavior was inconsistent | Review the mutant and the test — may be flaky |
| **Skipped** | Code was untestable (decorators, etc.) | Acceptable for infrastructure, not for domain |

---

## Workflow: Fixing Surviving Mutants

### Step 1: Identify survivors

```bash
uv run mutmut results --survived
```

### Step 2: Examine each survivor

```bash
uv run mutmut show 42  # Replace 42 with the mutant ID
```

This shows a diff like:

```diff
--- src/ingestion/domain/entities.py
+++ mutant
@@ -15,1 +15,1 @@
-    if self.amount > 0:
+    if self.amount >= 0:
```

### Step 3: Write a test that catches it

The surviving mutant above shows that no test checks the boundary condition
where `amount == 0`. Write a test:

```python
def test_amount_zero_is_invalid():
    """Boundary: amount=0 should be rejected, not just negative values."""
    with pytest.raises(ValueError):
        IngestionRecord(amount=0)
```

### Step 4: Verify the mutant is now killed

```bash
uv run mutmut run --paths-to-mutate src/ingestion/domain/entities.py
```

---

## Target Coverage by Layer

| Layer | Mutant Survival Target | Rationale |
|-------|----------------------|-----------|
| **Domain** | **0 survivors** | Core business logic must be fully tested |
| **Application** | **0 survivors** | Use case orchestration must be verified |
| **Infrastructure** | **< 1% survivors** | Some adapter code is hard to mutate (e.g., connection strings) |
| **Presentation** | **Not required** | Thin layer tested via integration/E2E tests |

---

## Common Mutation Patterns

### Arithmetic Mutations
`+` → `-`, `*` → `/`, `//` → `/`

**How to catch:** Test with known input/output pairs where the result differs.

### Comparison Mutations
`>` → `>=`, `==` → `!=`, `<` → `<=`

**How to catch:** Test boundary conditions (0, 1, -1, empty, max).

### Boolean Mutations
`True` → `False`, `and` → `or`, `not x` → `x`

**How to catch:** Test both branches of every conditional.

### Return Value Mutations
`return x` → `return None`, `return x` → `return x + 1`

**How to catch:** Assert on the exact return value, not just truthiness.

### Deletion Mutations
Statement removed entirely.

**How to catch:** Ensure the statement has an observable side effect tested.

---

## CI Integration

Add to your GitHub Actions workflow:

```yaml
- name: Mutation Testing (Domain)
  run: |
    uv run mutmut run --paths-to-mutate src/*/domain/ --CI
    uv run mutmut results
    # Fail if any mutants survived in domain layer
    survived=$(uv run mutmut results | grep -c "Survived" || true)
    if [ "$survived" -gt 0 ]; then
      echo "❌ $survived mutants survived in domain layer"
      uv run mutmut results --survived
      exit 1
    fi
```

---

## Tips

- **Start with domain layer** — that's where mutation testing has the highest ROI
- **Run on specific files** during development to keep feedback fast
- **Boundary conditions** are the #1 source of surviving mutants
- **Don't chase 0% in infrastructure** — some adapter mutations are not worth testing
- **Combine with `polyfactory`** to generate edge-case fixtures automatically
