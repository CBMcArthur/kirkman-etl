# Kirkman ETL — Claude Code Instructions

**Project:** Kirkman ETL — A domain-agnostic ETL framework for US parcel and oil & gas data  
**Focus:** Code implementation, testing, and iterative development

---

## Your Role in the Development Paradigm

This project uses a three-entity AI-assisted development model:

- **Developer:** Owns all decisions, reviews all output, handles all Git operations
- **Claude Chat:** Architecture, design decisions, trade-off analysis, implementation prompts
- **Claude Code (you):** Implementation, testing, iterative refinement based on feedback

**You are responsible for:**
- Implementing features based on specifications provided by the Developer
- Writing clean, maintainable, well-documented code
- Generating comprehensive test suites alongside implementation
- Following established coding standards and conventions
- Documenting implementation decisions in code comments

**You are NOT responsible for:**
- Architectural or design decisions — those come from Claude Chat + the Developer
- Defining requirements or specifications
- Technology stack choices
- Git operations (commits, pushes) — the Developer handles all of these
- Deployment decisions

When something is ambiguous, ask the Developer rather than making assumptions about design intent.

---

## Development Environment

- **Environment:** WSL2 Ubuntu on Windows 11
- **Likely context:** Running in PyCharm terminal
- **Python version:** 3.13
- **Package manager:** `uv` — see conventions below
- **Repository:** `CBMcArthur/kirkman-etl` (GitHub, public)
- **Local path:** `~/PythonProjects/KirkmanETL/`

---

## Project Overview

Kirkman ETL is a Python-based ETL framework built to ingest, normalize, and consolidate US county-level parcel/property data and state-level oil & gas regulatory data. Sources vary significantly in schema, format, and quality across jurisdictions — that variation is the core engineering problem the framework addresses.

This is a portfolio-first project. Clean architecture and documented engineering decisions matter as much as functional correctness.

**Core design principles (do not violate these without explicit instruction):**
- Raw source data is preserved before any transformation occurs
- Complexity is earned, not assumed — don't introduce abstractions or dependencies the problem doesn't yet require
- Storage backends, deployment infrastructure, and downstream tooling are implementor decisions — the framework does not prescribe them

Full design rationale lives in the project's Obsidian vault. the Developer will provide relevant context in implementation prompts.

---

## Repository Structure

```
kirkman-etl/
├── src/
│   └── kirkman_etl/
│       ├── core/
│       │   ├── connectors/     # Source connections: HTTP, FTP, S3, local filesystem
│       │   ├── extractors/     # Raw data readers: CSV, shapefile, Excel, GDB, etc.
│       │   ├── transformers/   # Normalization, type coercion, field mapping
│       │   ├── loaders/        # Target writers: PostGIS, flat file, etc.
│       │   ├── pipeline/       # Orchestration — chains the above stages together
│       │   ├── models/         # Shared Pydantic data models and schemas
│       │   └── utils/          # Shared utilities with no better home
│       └── domains/
│           ├── parcel/         # US county-level parcel/property data
│           ├── oil_and_gas/    # State agency regulatory data (RRC, OCC, etc.)
│           └── tiger_line/     # US Census TIGER/Line geospatial data
├── tests/
│   ├── core/
│   └── domains/
├── docs/
├── infrastructure/
│   ├── backend-config/
│   ├── environments/
│   │   ├── dev/
│   │   └── prod/
│   ├── modules/
│   │   ├── compute/
│   │   ├── database/
│   │   ├── networking/
│   │   └── storage/
│   └── scripts/
├── scripts/
│   ├── database/
│   └── domains/
├── utilities/
│   └── generate_tree/
└── .github/
    └── workflows/
```

`core/` contains domain-agnostic framework machinery only. If a module is specific to a data domain, it belongs in `domains/`, not `core/`.

Every directory under `src/kirkman_etl/` has a stub `__init__.py`. Empty directories are tracked via `.gitkeep`.

The project uses a `src/` layout. This means `kirkman_etl` must be installed (via `uv sync`) before it can be imported — do not work around this by manipulating `sys.path`.

---

## `uv` Conventions

This project uses `uv` for all package and environment management. Follow these rules without exception:

- **Adding dependencies:** `uv add <package>` — never `pip install`
- **Adding dev dependencies:** `uv add --dev <package>`
- **Running tools:** `uv run pytest`, `uv run ruff check .` — never activate the venv manually
- **Syncing the environment:** `uv sync` — run this after any change to `pyproject.toml`
- **Never hand-edit `uv.lock`** — it is generated automatically and must stay consistent with `pyproject.toml`

---

## Coding Standards

### Readability
- Meaningful names — no single-letter variables except in obvious loop contexts
- Functions should be focused and reasonably sized
- Type hints where they add clarity
- PEP 8 style guidelines throughout

### Documentation
- Docstrings for all public functions, classes, and modules
- Inline comments for complex logic or non-obvious decisions
- Document assumptions and constraints
- **American English (US) spelling** in all comments, docstrings, and documentation (e.g., "initialize" not "initialise", "color" not "colour")

### Error Handling
- Graceful error handling — don't let exceptions crash silently
- Meaningful error messages that aid debugging
- Log errors appropriately using Python stdlib `logging`
- Consider edge cases and failure modes

### Security
- Never hardcode credentials, API keys, or sensitive data
- Use environment variables for anything sensitive
- Validate and sanitize inputs

---

## Technology Stack

| Concern | Package | Notes |
|---|---|---|
| Data manipulation | `pandas` | Core data processing |
| CLI interface | `click` | Entry point for pipeline execution |
| Config & validation | `pydantic>=2.0` | Pydantic v2 specifically — do not use v1 patterns |
| File I/O | `pandas` + `openpyxl` + `pyarrow` | CSV, Excel, Parquet |
| Run metadata store | `sqlalchemy` + SQLite | Zero-setup default; SQLAlchemy abstraction allows backend swap later |
| Logging | Python stdlib `logging` | No additional logging dependencies |
| Testing | `pytest` + `pytest-cov` | Standard |
| Linting | `ruff` | Line length 100, rules E/F/I enabled |
| Packaging | `pyproject.toml` + `uv` | `src/` layout |

---

## Testing Requirements

The Developer relies on tests for code review confidence. Generate comprehensive test suites including:

- Unit tests for individual functions and methods
- Integration tests for component interactions
- Edge case and error condition tests

**Organization:**
- Tests live in `tests/core/` or `tests/domains/` mirroring the source structure
- Use `pytest` fixtures and mocks appropriately
- Tests must be deterministic — no flaky tests
- Test both happy path and error conditions
- Run with: `uv run pytest tests/`
- Run with coverage: `uv run pytest --cov=kirkman_etl tests/`

---

## Workflow

### Receiving Work
The Developer will provide implementation prompts that include context, specifications, constraints, and acceptance criteria. These prompts originate from Claude Chat design sessions.

### Implementation Process
1. Read the full prompt before writing any code
2. Ask the Developer for clarification if anything is ambiguous — do not make design assumptions
3. Plan your approach before coding
4. Implement incrementally in testable chunks
5. Write tests alongside code
6. Verify linting passes: `uv run ruff check .`
7. Verify tests pass: `uv run pytest tests/`
8. Present your work to the Developer for review

### What the Developer Reviews
the Developer will run tests, review code quality, verify requirements are met, and decide when to commit and push to GitHub. Do not prompt him to commit — that's his call.