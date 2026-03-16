# Architecture Diagram — As-Built v4.x

## Implemented runtime flow (current)

```text
Orchestrator (orchestrator.py)
  ├─ init_schema_v4()
  ├─ UniverseBuilder (discovery/universe_builder.py)
  ├─ KalshiRESTAdapter (adapters/kalshi_rest_adapter.py)
  ├─ CryptoS3Adapter (adapters/crypto_s3_adapter.py)
  ├─ CryptoMarketLocator (discovery/market_locator.py)
  ├─ SnapshotPipeline (pipelines/snapshot_pipeline.py)
  ├─ Engine (engine/main.py)
  └─ DashboardService (dashboard/service.py)

Engine loop:
  1) snapshot_pipeline.run()
  2) health_pipeline.run()
  3) insert metrics_record row
  4) sleep(loop_interval)
```

## Implemented data flow (current)

```text
Kalshi REST + Crypto S3
      │
      ▼
SnapshotPipeline
  ├─ market_snapshot
  ├─ weather_snapshot
  └─ crypto_snapshot
      │
      ▼
database/db.py + schema_v4.sql (ute_trading.db)
      │
      ▼
DashboardQueries -> DashboardService -> typed view models
```

## Implemented discovery flow (current)

```text
series.json -> UniverseBuilder -> crypto buckets/weather buckets
                     │
                     ▼
               CryptoTaxonomy
                     │
                     ▼
              CryptoMarketLocator
                     │
                     ▼
           active ticker resolution
```

## Legacy / retained surfaces

- `archive/` tree (legacy weather/oracle/adapters)
- `dashboard/dashboard.py` legacy Flask path
- root-level `database.py` legacy DB layer
- `run_all.py` legacy multi-engine entrypoint (references missing coinbase engine)

## Planned (not fully wired yet)

- Risk pipeline integrated in live loop
- Execution pipeline integrated in live loop
- Position/PnL service integration in live loop
- Dedicated alerting + SLO monitor modules

Use this file as architectural truth for **current runtime behavior**, not target-state design.