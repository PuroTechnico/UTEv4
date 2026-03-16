# Onboarding Guide — As-Built v4.x

## 1) What you should understand first

UTE currently runs a **snapshot + health loop** orchestrated by `orchestrator.py`.

If you assume risk/execution/position services are live-loop integrated, you will misread current behavior.

## 2) Prerequisites

- Python 3.10+
- Linux shell access
- Kalshi API credentials + private key file
- SQLite CLI (recommended)

## 3) Environment setup

```bash
cd /home/maureces/ute
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set environment variables (current code expects these names):

```bash
export KALSHI_API_KEY="<your_key_id>"
export KALSHI_BASE_URL="https://api.elections.kalshi.com"
```

Private key location used by default in `orchestrator.py`:

```text
~/.secrets/kalshi/kalshi_full_key.pem
```

## 4) Initialize + run the system

Canonical run path:

```bash
cd /home/maureces/ute
source venv/bin/activate
python orchestrator.py
```

This path initializes schema (`init_schema_v4`) and starts the engine loop.

## 5) Validate ingestion quickly

Run one snapshot cycle:

```bash
python scripts/run_snapshot_check.py
```

Run readiness summary checks:

```bash
python scripts/run_production_checklist.py
```

## 6) Database verification

```bash
sqlite3 ute_trading.db
```

Then:

```sql
.tables
SELECT COUNT(*) FROM market_snapshot;
SELECT COUNT(*) FROM weather_snapshot;
SELECT COUNT(*) FROM crypto_snapshot;
SELECT COUNT(*) FROM health_snapshot;
SELECT * FROM health_snapshot ORDER BY timestamp DESC LIMIT 5;
```

## 7) Runtime components (implemented)

- `SnapshotPipeline` fetches:
  - active crypto markets via locator
  - weather snapshots
  - crypto S3 snapshots
- `HealthPipeline` writes heartbeat and venue status rows
- `Engine` records loop metrics

## 8) Components not fully integrated yet

- Risk pipeline in live loop
- Execution pipeline in live loop
- Position/PnL service in live loop
- Dedicated alerting service modules

## 9) Legacy components to avoid for primary onboarding

- `run_all.py` (references missing coinbase engine)
- root `database.py` (legacy DB layer)
- most of `archive/`
- `dashboard/dashboard.py` (legacy Flask path)

## 10) Common onboarding pitfalls

1. Using the wrong entrypoint (`python -m ute.engine.main` from old docs)
2. Expecting execution/trades from current loop without additional wiring
3. Assuming `requirements.txt` fully matches all imports
4. Editing legacy modules under `archive/` instead of active runtime modules

Use this guide as the authoritative new-hire path until the next architecture cut.