# CHANGELOG — UTE Documentation and Architecture Notes

## 2026-03-15 — Documentation Realignment (As-Built v4.x)

### Added

- As-built documentation baseline across all core docs.
- Explicit implemented-vs-planned labeling.
- Practical operator and onboarding run paths using `orchestrator.py`.

### Changed

- Rewrote architecture/dependency docs to match actual repository modules.
- Rewrote onboarding and operations docs with executable commands currently available.
- Rewrote roadmap language to avoid presenting planned modules as already live.
- Rewrote alerting/SLO spec to reflect current measurable signals and current automation limits.

### Clarified

- Current live loop is snapshot + health + loop metrics.
- Risk/execution/position/alerting are not yet fully wired in canonical runtime path.
- `archive/` is retained legacy code, not active runtime surface.
- Root-level `database.py` is legacy relative to active `database/db.py` path.

---

## Historical notes (retained)

Earlier documentation labeled many components with v4.x/v4.4/v3.2 version tags and future-state architecture diagrams. That content represented a blend of implemented work and forward roadmap material. The current docs set is now normalized to state what is implemented today.