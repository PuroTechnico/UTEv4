# Module Dependency Map — As-Built v4.x

This is the practical dependency map for the repository state in March 2026.

## 1) Active module groups

```text
adapters/
discovery/
time_utils/
pipelines/
engine/
health/
dashboard/
database/
models/
scripts/
```

Legacy-only group:

```text
archive/
```

## 2) Canonical dependency directions (implemented)

```text
adapters -> discovery
discovery -> time_utils
discovery -> adapters
pipelines -> discovery, adapters, models, database
engine -> pipelines, health, database
health -> database, models
dashboard -> database, models, adapters(crypto_s3)
database -> stdlib
models -> stdlib
scripts -> orchestrator/pipelines/database
```

## 3) Key file-level dependencies

- `orchestrator.py`
  - imports `Engine`, `SnapshotPipeline`, `DashboardService`, `KalshiRESTAdapter`, `CryptoS3Adapter`, `CryptoMarketLocator`, `build_universe`, `init_schema_v4`
- `engine/main.py`
  - imports `HealthPipeline`, `database.db.insert`
- `pipelines/snapshot_pipeline.py`
  - imports `MarketSnapshot`, `KalshiRESTAdapter`, `CryptoS3Adapter`, `CryptoMarketLocator`, DB helpers
- `dashboard/service.py`
  - imports `DashboardQueries`, view models, `CryptoS3Adapter`
- `dashboard/queries.py`
  - imports `database.query` + typed models

## 4) Forbidden / discouraged dependencies

- `database/` importing business modules
- `models/` importing runtime services
- `dashboard/` writing to DB directly
- `archive/` imported by active runtime paths

## 5) Known boundary violations / drift to resolve

- Two DB layers exist (`database/db.py` active, root `database.py` legacy)
- Legacy Flask dashboard module imports `weather_oracle` surface
- `run_all.py` references missing `engine.coinbase_engine`

## 6) Planned modules not currently present

The following are documented in older docs but are **not currently present as top-level active modules**:

- `execution/`
- `alerting/`
- `slo_monitor/`

Treat those as roadmap items unless and until code appears in repo and is wired through `orchestrator.py`.