# Operations Manual — As-Built v4.x

## 1) Production process model (current)

Primary runtime process:

- `python orchestrator.py`

This process currently executes:

1. `SnapshotPipeline.run()`
2. `HealthPipeline.run()`
3. metrics insert
4. sleep interval

## 2) Startup SOP

```bash
cd /home/maureces/ute
source venv/bin/activate
python orchestrator.py
```

Pre-flight checks:

- Kalshi key env var exists (`KALSHI_API_KEY`)
- private key file exists at expected path
- DB path writable (`ute_trading.db`)

## 3) Liveness + freshness checks

```bash
python scripts/run_snapshot_check.py
python scripts/run_production_checklist.py
```

Manual SQL checks:

```sql
SELECT timestamp FROM health_snapshot ORDER BY timestamp DESC LIMIT 1;
SELECT COUNT(*) FROM market_snapshot;
SELECT COUNT(*) FROM weather_snapshot;
SELECT COUNT(*) FROM crypto_snapshot;
```

## 4) Log and diagnostics guidance

- Primary runtime logs are standard output unless redirected.
- Existing `logs/` files may include historical output from earlier generations.
- If running via service manager, capture stdout/stderr to dedicated files.

## 5) Incident runbooks

### A. Engine process exits/crashes

1. Verify credential env + key path
2. Re-run `python scripts/run_snapshot_check.py`
3. Restart `python orchestrator.py`
4. Confirm `health_snapshot` updates

### B. No new market snapshots

1. Validate Kalshi API reachability
2. Check locator behavior for empty active market sets
3. Confirm `series.json` freshness in `data/kalshi_universe/series.json`

### C. DB write errors / lock issues

1. Ensure single writer process for same DB file
2. Run `VACUUM` during maintenance window
3. Restart orchestrator process

### D. Unexpected lack of trades

Current loop does not fully integrate live execution/risk as a canonical production flow.
Treat this as expected unless execution integration work has been explicitly deployed.

## 6) Maintenance schedule

Weekly:

- DB size check
- integrity check
- snapshot freshness sanity test

Monthly:

- requirements/import drift review
- archive/runtime boundary review
- docs accuracy review

## 7) Service management template (example)

```ini
[Unit]
Description=UTE Orchestrator

[Service]
WorkingDirectory=/home/maureces/ute
ExecStart=/home/maureces/ute/venv/bin/python orchestrator.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## 8) Legacy surfaces

Treat these as non-canonical for operations unless explicitly reactivated:

- `run_all.py`
- root `database.py`
- most of `archive/`
- `dashboard/dashboard.py`

This manual is intentionally scoped to what operators can run and verify today.