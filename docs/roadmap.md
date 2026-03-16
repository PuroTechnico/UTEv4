# Roadmap — As-Built v4.x to Next Stable Cut

## Current state (March 2026)

Implemented and wired:

- Orchestrator bootstrapping (`orchestrator.py`)
- Universe build + taxonomy + locator flow (`discovery/`)
- Snapshot ingestion (`pipelines/snapshot_pipeline.py`)
- Health writes (`health/health_pipeline.py`)
- Typed DB persistence via `database/db.py` and `schema_v4.sql`
- Dashboard query/service typed assembly (`dashboard/queries.py`, `dashboard/service.py`)

Partially implemented but not fully integrated in canonical live loop:

- Strategy/risk/execution lifecycle as one deterministic pipeline
- Position and PnL lifecycle integration
- Dedicated alerting/SLO modules

## Phase 1 (near-term, highest priority)

1. **Runtime consolidation**
   - Make `orchestrator.py` the only canonical live entrypoint.
   - Remove/flag broken entrypoints (`run_all.py`) from normal operations.

2. **Dependency reconciliation**
   - Align `requirements.txt` with actual imports used in active modules/tests.

3. **Health hardening**
   - Replace stub venue status writes with real connectivity probes.

## Phase 2 (integration)

1. **Strategy-to-execution integration**
   - Wire strategy outputs into validated risk gate and execution path.

2. **Position/PnL integration**
   - Persist and verify position + PnL updates in same loop lifecycle.

3. **Operational guardrails**
   - Add explicit failure handling policy for snapshot fetch failures and DB write issues.

## Phase 3 (observability and safety)

1. **SLO automation**
   - Implement alerting monitor that evaluates freshness and heartbeat thresholds.

2. **Alert transport**
   - Add destination routing (e.g., Slack/PagerDuty) with dedupe/rate limits.

3. **Runbook automation**
   - Convert manual checks into executable health checks and CI sanity jobs.

## Phase 4 (cleanup and debt reduction)

1. **Legacy boundary cleanup**
   - Isolate or remove obsolete runtime paths (`database.py`, legacy dashboard route, archive-referenced imports).

2. **Docs + code contract**
   - Enforce implemented/planned tags in docs updates.
   - Add lightweight architecture validation checks.

## Phase 5 (optional expansion)

- Distributed runners by category
- Centralized execution service
- Real-time dashboard streaming

These are future options and should not be treated as present architecture until merged and wired.