# SRM Core ??? Internal Changelog

Per-packet record of changes for implementation tracking. Public-facing release notes may be derived from this log later.

---

## Template

Copy this block for each completed packet:

```markdown
## Packet NN ??? <Name> (YYYY-MM-DD)

**Commit:** `<short-hash>` on `develop`

### Summary
- ...

### Files changed
- ...

### Migration / tests
- migrate: PASS | FAIL
- run-tests: PASS | FAIL

### Notes / follow-ups
- ...
```

---

## Packet 00 ??? Structure baseline (2026-07-02)

**Commit:** _(see develop HEAD after push)_

### Summary
- Added `docs/BUILD_PLAN.md` as single source of truth for SRM scope and packet roadmap.
- Added `docs/DECISIONS.md` with ADR template and initial decisions.
- Added `docs/CHANGELOG_INTERNAL.md` (this file) with changelog template.
- Updated `.gitignore` to exclude `__pycache__/`, `*.pyc`, `*.pyo`, `*.log`, `.venv/`, `.env`.
- Verified no tracked `__pycache__/` or `*.pyc` artifacts.

### Files changed
- `docs/BUILD_PLAN.md` (new)
- `docs/DECISIONS.md` (new)
- `docs/CHANGELOG_INTERNAL.md` (new)
- `.gitignore` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS (0 tests ??? no test modules yet)

### Notes / follow-ups
- Packet 01 (Geographic Area DocType) is next per BUILD_PLAN.

