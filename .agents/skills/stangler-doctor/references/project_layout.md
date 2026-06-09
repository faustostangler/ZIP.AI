# Standard Project Layout — Hexagonal Modular Monolith

This is the canonical directory structure for projects following the Stangler Method.
Each Bounded Context is a self-contained module with its own Hexagonal layers.

---

## Root Structure

```
project-root/
├── .agents/                    # AI skills and automation
│   └── skills/
├── .github/
│   └── workflows/              # CI/CD pipelines (GitHub Actions)
├── docs/
│   ├── adr/                    # Architectural Decision Records
│   │   └── ADR-001-example.md
│   └── GLOSSARY.md             # Ubiquitous Language definitions
├── src/
│   ├── __init__.py
│   ├── config.py               # Centralized Pydantic Settings (single class)
│   ├── main.py                 # Composition Root — wire adapters here
│   ├── shared_kernel/          # Cross-context shared types
│   │   ├── __init__.py
│   │   ├── types.py            # Common Value Objects, IDs
│   │   └── events.py           # Domain Events (if using event-driven)
│   ├── <bounded_context_1>/    # e.g., ingestion/
│   │   ├── __init__.py
│   │   ├── domain/             # Pure Domain Layer
│   │   │   ├── __init__.py
│   │   │   ├── entities.py     # Entities with identity
│   │   │   ├── value_objects.py # Immutable Value Objects
│   │   │   ├── specifications.py # Query specifications
│   │   │   └── exceptions.py   # Domain-specific exceptions
│   │   ├── application/        # Application Layer
│   │   │   ├── __init__.py
│   │   │   ├── ports.py        # Port interfaces (ABCs)
│   │   │   └── use_cases.py    # Use Case orchestration
│   │   ├── infrastructure/     # Infrastructure Layer
│   │   │   ├── __init__.py
│   │   │   ├── adapters/       # Adapter implementations
│   │   │   │   ├── __init__.py
│   │   │   │   ├── postgres_adapter.py
│   │   │   │   ├── redis_adapter.py
│   │   │   │   └── sentry_adapter.py
│   │   │   └── translators/    # Specification translators
│   │   │       └── duckdb_translator.py
│   │   └── presentation/       # Presentation Layer (thin)
│   │       ├── __init__.py
│   │       ├── api.py          # FastAPI router
│   │       └── schemas.py      # API request/response schemas
│   └── <bounded_context_2>/    # Same structure per context
├── tests/                      # Mirrors src/ structure exactly
│   ├── __init__.py
│   ├── conftest.py             # Shared fixtures, factories
│   ├── <bounded_context_1>/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   └── test_entities.py
│   │   ├── application/
│   │   │   └── test_use_cases.py
│   │   └── infrastructure/
│   │       └── test_adapters.py
│   └── integration/            # Cross-context integration tests
│       └── test_ingestion_flow.py
├── playground/                 # Exploratory scripts, notebooks
├── scripts/                    # Operational scripts (migrations, seeds)
├── .env                        # Environment variables (never committed)
├── .env.example                # Template for .env (committed)
├── Dockerfile                  # Single image, multi-role via entrypoint
├── docker-compose.yml          # Local + CI service orchestration
├── pyproject.toml              # uv, hatch, pytest, mutmut, ruff config
├── Makefile                    # Developer convenience commands
└── README.md
```

---

## Layer Rules (Enforced)

### Domain Layer (`domain/`)
- **ZERO** framework imports (no FastAPI, no SQLAlchemy, no Pydantic `BaseSettings`)
- `Pydantic BaseModel` is allowed for Value Objects (it's a data library, not a framework)
- Pure Python + `typing` + `abc` only
- No I/O operations whatsoever

### Application Layer (`application/`)
- Defines **Ports** as `abc.ABC` abstract classes
- **Use Cases** orchestrate domain objects via dependency-injected ports
- No concrete adapter imports — only Port interfaces
- Returns domain objects or DTOs, never framework-specific types

### Infrastructure Layer (`infrastructure/`)
- **Adapters** implement Port interfaces
- All I/O happens here: database, cache, HTTP, file system
- Contains **Translators** (e.g., `DuckDBSpecificationTranslator`) for Specification Pattern
- Name-Based Fallback pattern mandatory in `match/case` blocks

### Presentation Layer (`presentation/`)
- **Humble Object Pattern**: Thin wrapper that delegates to Use Cases
- FastAPI routers define endpoints, schemas handle serialization
- Complex UI logic extracted to testable pure Python adapters
- No business logic — only request/response mapping

---

## Composition Root (`main.py`)

This is the only place where concrete adapters are wired to ports:

```python
# src/main.py — Composition Root
from src.config import Settings
from src.ingestion.application.use_cases import IngestCSVUseCase
from src.ingestion.infrastructure.adapters.postgres_adapter import PostgresAdapter

settings = Settings()  # Validates .env at startup (fail-fast)

# Wire adapters to ports
persistence_adapter = PostgresAdapter(settings.database_url)
ingest_use_case = IngestCSVUseCase(persistence_port=persistence_adapter)
```

---

## Import Rules

```python
# ✅ CORRECT — relative or absolute without src. prefix
from ingestion.domain.entities import IngestionRecord
from ingestion.application.ports import PersistencePort

# ❌ WRONG — never use src. prefix inside src/
from src.ingestion.domain.entities import IngestionRecord
```

---

## Test Structure

Tests mirror `src/` exactly. Each test file tests one module:

```
tests/ingestion/domain/test_entities.py      → src/ingestion/domain/entities.py
tests/ingestion/application/test_use_cases.py → src/ingestion/application/use_cases.py
tests/ingestion/infrastructure/test_adapters.py → src/ingestion/infrastructure/adapters/
```

Use `polyfactory` to generate Pydantic model fixtures automatically.
Use `conftest.py` for shared mocks and factory registrations.
