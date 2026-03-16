## Summary
- What changed?
- Why now?

## Type of Change
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation
- [ ] CI/CD

## Trading/Data Impact
- [ ] No impact to live runtime path
- [ ] Snapshot pipeline behavior changed
- [ ] Discovery/locator behavior changed
- [ ] Data model/schema changed
- [ ] External API integration changed (Kalshi/Coinbase/S3)

## Risk Checklist
- [ ] No secrets or credential files included
- [ ] No generated logs/data artifacts tracked
- [ ] No file >95MB tracked
- [ ] Backward compatibility considered

## Validation Performed
- [ ] CI checks pass
- [ ] Offline smoke test pass
- [ ] Local runtime sanity check pass (`python scripts/run_snapshot_check.py`)
- [ ] Production checklist script pass (`python scripts/run_production_checklist.py`)

## Notes for Reviewers
- Key files to review:
- Follow-up tasks:
