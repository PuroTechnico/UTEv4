# Alerting and SLO Spec — As-Built v4.x

## Purpose

Define measurable reliability targets for the currently implemented runtime.

This document distinguishes:

- **Implemented measurements**
- **Planned alerting modules**

## 1) Implemented SLO signals (current)

### 1.1 Heartbeat freshness

Source: `health_snapshot` rows written by `health/health_pipeline.py`.

- Target: new heartbeat within 10 seconds
- Warning: > 15 seconds stale
- Critical: > 30 seconds stale

### 1.2 Snapshot freshness

Source tables:

- `market_snapshot`
- `weather_snapshot`
- `crypto_snapshot`

Targets:

- Warning if no new rows for 30 seconds
- Critical if no new rows for 60 seconds

### 1.3 Loop completion signal

Source: `metrics_record` insert cadence in `engine/main.py`.

- Target: each loop produces one fresh metrics row
- Warning if stale > 30 seconds

## 2) Implemented health coverage

Current health pipeline writes:

- `component=engine` heartbeat
- stub venue health rows for `kalshi`, `coinbase`, `weather`

Note: venue checks are currently placeholder status rows, not full connectivity probes.

## 3) Alert transport (current state)

No dedicated in-repo production alert transport module is fully wired yet.

Operationally today, alerts are implemented via:

- SQL freshness checks
- script-based checks (`scripts/run_production_checklist.py`)
- operator log monitoring

## 4) Planned alerting expansion

Planned but not yet canonicalized as top-level active modules:

- `alerting/` (routing, dedupe, severity policy)
- `slo_monitor/` (windowing, threshold evaluation)
- external channels (Slack/PagerDuty) integration

## 5) Minimal daily operator checklist

1. Verify heartbeat freshness
2. Verify snapshot tables are increasing
3. Verify process uptime
4. Verify no sustained DB write failures

## 6) SLO policy guidance

Until alerting modules are integrated, treat this SLO spec as an operational monitoring contract, not an automated enforcement system.