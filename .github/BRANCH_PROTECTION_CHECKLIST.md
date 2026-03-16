# Branch Protection Checklist (main)

Use this checklist in GitHub settings for a professional baseline.

## 1) Protect branch

- Enable **Require a pull request before merging**
- Enable **Require approvals** (recommended: 1)
- Enable **Dismiss stale pull request approvals when new commits are pushed**
- Enable **Require conversation resolution before merging**

## 2) Require status checks

Set these required checks:

- `Python Static Checks`
- `Repo Hygiene Checks`

## 3) Restrict direct pushes

- Enable **Restrict who can push to matching branches**
- Keep automation/users minimal

## 4) Keep history clean

- Enable **Require linear history**
- Disable force pushes (except admins only, if needed for emergencies)
- Disable branch deletion protection override unless required

## 5) Optional but recommended

- Enable **Require signed commits**
- Enable **Require deployments to succeed before merging** (if using environments)
- Add a CODEOWNERS file for critical paths (`engine/`, `pipelines/`, `database/`, `.github/workflows/`)

## 6) Merge settings

Repository Settings -> General -> Pull Requests:

- Prefer **Squash merge** for cleaner history
- Optionally disable merge commits/rebase merges

## 7) Security/secret hygiene

- Enable secret scanning and push protection
- Keep `.env` untracked (already enforced in CI)
- Keep `data/logs/` and large generated artifacts out of git
