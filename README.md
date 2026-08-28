# Web Signal Intelligence Pipeline

A compact data-mining/backend project inspired by the engineering problems behind large-scale B2B data products: ingesting crawl observations, normalizing entities, deduplicating repeated pages, tracking technology signals over time, and serving the latest state through a query API.

The project is intentionally **not** a web scraper. It starts where a crawler hands off data: newline-delimited crawl observations. That keeps the focus on the parts that matter for data-platform engineering - transformation, entity resolution, idempotent loads, data modeling, change history, SQL and operational correctness.

## Stack

Python 3.12 · PostgreSQL · SQLAlchemy 2 · FastAPI · Pydantic v2 · SQL · Pytest · Docker Compose · GitHub Actions · Linux-friendly CLI

## What it does

1. Reads crawl observations from JSONL.
2. Canonicalizes URLs/domains and normalizes technology names.
3. Generates deterministic content fingerprints to make repeated imports idempotent.
4. Resolves observations into company entities by canonical domain.
5. Stores append-only observations and normalized technology signals.
6. Derives change events when a company's observed technology set changes.
7. Exposes search, company detail, history and aggregate statistics through FastAPI.
8. Supports batch ingestion and a synthetic-data benchmark for repeatable validation.

## Architecture

```text
JSONL crawl feed
      |
      v
Normalizer / fingerprinting
      |
      v
Incremental ETL pipeline -----> rejected/duplicate counters
      |
      v
Repository abstraction
   |             |
   v             v
PostgreSQL     Memory repo
(production)   (tests/benchmark)
   |
   +--> companies
   +--> observations
   +--> technology_signals
   +--> change_events
      |
      v
FastAPI query service
```

## Core engineering decisions

- **Idempotency:** each observation has a SHA-256 fingerprint based on canonical domain, normalized URL, capture timestamp and normalized payload. Re-importing the same feed does not duplicate data.
- **Entity resolution:** the canonical domain is the stable company key. This is deterministic and easy to audit.
- **Append-only observations:** raw facts are retained instead of overwriting the past. Latest state is derived from observations.
- **Normalized technologies:** aliases such as `postgres`, `postgresql` and `PostgreSQL` map to one canonical value.
- **Change history:** a new observation is compared with the previous technology set and produces `technology_added` / `technology_removed` events.
- **Batch-oriented ingestion:** records are processed in configurable chunks rather than loaded as one unbounded list.
- **Database indexes:** domain, observation time, fingerprint and technology lookup paths are indexed for common query patterns.

## Quick start with PostgreSQL

```bash
cp .env.example .env
docker compose up -d db
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python -m websignal.cli init-db
python -m websignal.cli ingest data/sample_crawl.jsonl
uvicorn websignal.api:app --reload
```

Swagger: `http://localhost:8000/docs`

## Example API calls

```bash
curl 'http://localhost:8000/companies?technology=python&limit=20'
curl 'http://localhost:8000/companies/acme.example'
curl 'http://localhost:8000/companies/acme.example/history'
curl 'http://localhost:8000/stats'
```

## Benchmark / deterministic validation

The benchmark uses an in-memory repository so it can validate transformation, deduplication, entity resolution and change-event logic without requiring a database server:

```bash
python -m websignal.cli benchmark --records 10000 --seed 7
```

## PostgreSQL model

- `companies` - one row per canonical domain.
- `observations` - append-only crawl observations with a unique fingerprint.
- `technology_signals` - normalized many-to-many technology facts per observation.
- `change_events` - derived technology additions/removals for audit/history.

See [`docs/data_model.md`](docs/data_model.md) and [`docs/scaling_notes.md`](docs/scaling_notes.md).

## Tests

```bash
pytest
```

Coverage focuses on normalization, alias handling, idempotent ingestion, change detection, filtering/pagination and API behavior. PostgreSQL-specific SQL is generated through SQLAlchemy and the production repository uses explicit transactions and `ON CONFLICT` upserts.

## Why this is more than CRUD

The interesting problem is not storing a `Company` row. It is turning noisy repeated observations into a stable, queryable timeline: canonicalizing identifiers, deduplicating imports, preserving history, detecting changes, keeping ingestion idempotent and structuring data for read-heavy queries. Those are the same classes of problems that appear in web/data-mining systems at much larger scale.
