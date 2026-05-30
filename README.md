# Kirkman ETL

A domain-agnostic ETL framework for ingesting and normalizing US county-level parcel/property data
and state-level oil & gas regulatory data. The core engineering problem is that source schemas,
file formats, and data quality vary significantly across jurisdictions — Kirkman ETL addresses this
with a layered pipeline architecture that separates raw data preservation from transformation logic.
This is a portfolio project built to demonstrate clean ETL architecture and engineering discipline
in a messy, real-world data domain.

---

## Architecture

The framework is organized into two top-level layers:

- **`core/`** — domain-agnostic pipeline machinery: connectors, extractors, transformers, loaders,
  and the orchestration layer that chains them together. Nothing in `core/` knows about parcels or
  oil and gas.
- **`domains/`** — domain-specific implementations that extend the core abstractions for each data
  domain (`parcel/`, `oil_and_gas/`, `tiger_line/`).

Data flows through the pipeline in one direction:

```
Source → Raw Preservation → Extract → Transform → Load → Destination
```

Raw source data is always written to disk before any transformation occurs. This is a hard
architectural constraint — it makes debugging and re-processing possible without re-fetching from
the source.

---

## Tech Stack

| Tool | Version | Why |
|---|---|---|
| Python | 3.13 | Latest stable; type system improvements matter for a schema-heavy project |
| uv | latest | Fast, lockfile-based dependency management — deterministic environments |
| pandas | ≥3.0 | Standard for tabular data manipulation at this scale |
| Pydantic | v2 | Schema validation and type coercion at pipeline boundaries |
| Click | ≥8 | Clean CLI interface for pipeline execution |
| SQLAlchemy | ≥2.0 | Abstracts the run-metadata store — SQLite by default, swappable later |
| SQLite | stdlib | Zero-setup run metadata store for development |
| PyArrow / Parquet | ≥24 | Efficient columnar storage for processed outputs |
| openpyxl | ≥3.1 | Excel source support — common in government data releases |

---

## Project Status

Phase 0 scaffold is in place. Directory structure, tooling, CI, and dependency configuration are
complete. Framework core (base classes, pipeline orchestration, connectors) is in progress.

---

## Development Setup

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/CBMcArthur/kirkman-etl.git
cd kirkman-etl
uv sync
```

Verify the environment:

```bash
uv run python --version   # should print Python 3.13.x
uv run pytest tests/      # should exit cleanly
uv run ruff check .       # should report no issues
```

---

## Development Paradigm

This project is developed using a three-entity AI-assisted workflow. The Developer owns all
decisions and handles all Git operations. Claude Chat (Anthropic) is used for architecture and
design sessions — working through trade-offs, producing implementation specs. Claude Code
(Anthropic) handles implementation, testing, and iterative refinement based on those specs.

This separation keeps design intent explicit and documented rather than embedded silently in
generated code. Implementation prompts live in the project's Obsidian vault alongside design
rationale.
