# UTE Docs — As-Built v4.x (March 2026)

This documentation set describes the repository **as it exists today**.

## What UTE currently is

UTE is a Kalshi-focused trading data/runtime project centered on:

- `orchestrator.py` as the primary runtime entrypoint
- `pipelines/snapshot_pipeline.py` for market/weather/crypto snapshot ingestion
- `engine/main.py` for loop orchestration (snapshot + health)
- `health/health_pipeline.py` for heartbeat + basic venue health rows
- `database/db.py` + `database/schema_v4.sql` as the active typed DB layer
- `dashboard/service.py` + `dashboard/queries.py` for typed view-model assembly

## Current execution scope (important)

Implemented in the active loop:

1. Snapshot pipeline run
2. Health pipeline run
3. Loop metrics insert

Not yet integrated into the active loop:

- Risk pipeline
- Execution engine
- Position service sync
- Alerting service / SLO monitor service

These are roadmap items or partially implemented components, not current end-to-end runtime behavior.

## Current repo layout (practical view)

- `adapters/` — Kalshi REST/WS + Crypto S3 adapters
- `discovery/` — taxonomy, market locator, universe builder, series updater
- `time_utils/` — active ticker helpers
- `pipelines/` — snapshot pipeline
- `engine/` — engine loop + strategy-related modules
- `health/` — health pipeline
- `dashboard/` — query + service layer; includes one legacy Flask path
- `database/` — active DB module and schema
- `models/` — typed dataclasses
- `archive/` — legacy code retained for reference, not canonical runtime

## Canonical run path (as-built)

```bash
cd /home/maureces/ute
source venv/bin/activate
python orchestrator.py
```

Useful validation scripts:

```bash
python scripts/run_snapshot_check.py
python scripts/run_production_checklist.py
```

## Dependency reality (as of March 2026)

Code currently imports and uses packages beyond `requirements.txt` in some areas.

Commonly used in active paths:

- `aiohttp`
- `cryptography`
- `requests`
- `python-dotenv`
- `pytz`

Used in weather/dashboard/legacy surfaces:

- `httpx`
- `flask`
- `jwt` (tests)

Treat `requirements.txt` as needing reconciliation with code imports.

## Legacy and compatibility notes

- `archive/` contains prior-generation weather/adapters/oracle paths.
- `database.py` (repo root) is an older DB layer; `database/db.py` is the active one for current typed flow.
- `run_all.py` references non-present coinbase engine modules and is not a reliable entrypoint for current runtime.

## Document conventions in this docs set

Each document now labels content as one of:

- **Implemented (as-built)**
- **Legacy / retained**
- **Planned**

This prevents roadmap content from being mistaken as production behavior.