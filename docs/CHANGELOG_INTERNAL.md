# SRM Core ? Internal Changelog

Per-packet record of changes for implementation tracking. Public-facing release notes may be derived from this log later.

---

## Template

Copy this block for each completed packet:

```markdown
## Packet NN ? <Name> (YYYY-MM-DD)

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

## Packet 00 ? Structure baseline (2026-07-02)

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
- run-tests: PASS (0 tests ? no test modules yet)

### Notes / follow-ups
- Packet 01 (Core DocTypes skeleton) is next per BUILD_PLAN.

---

## Packet 01 ? Core DocTypes skeleton (2026-07-02)

**Commit:** _(see develop HEAD)_

### Summary
- Added submittable DocTypes: SRM Incident, SRM Investigation.
- Added non-submittable DocType: SRM Sentiment Capture.
- Used `geographic_area_text` (Data) because Geographic Area DocType does not exist yet.
- Added baseline validation on SRM Incident (IKS consent, resolution summary on submitted Resolved/Closed).
- Added baseline validation on SRM Investigation (target close date vs opened on).
- Added System Manager permissions on all three DocTypes.
- Added `test_core_doctypes.py` with 3 validation tests.

### Files changed
- `srm_core/srm_core/doctype/__init__.py` (new)
- `srm_core/srm_core/doctype/srm_incident/` (new)
- `srm_core/srm_core/doctype/srm_investigation/` (new)
- `srm_core/srm_core/doctype/srm_sentiment_capture/` (new)
- `srm_core/srm_core/tests/` (new)
- `docs/CHANGELOG_INTERNAL.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS (3 tests in 0.857s)

### Notes / follow-ups
- Replace `geographic_area_text` with Link to Geographic Area when that DocType is added.
- Additional roles and workspace links deferred to later packets.

---

## Packet 02 ? Incident/Investigation lifecycle workflow (2026-07-02)

**Commit:** _(see develop HEAD)_

### Summary
- Added `srm_core/services/statuses.py` with shared incident/investigation status constants.
- SRM Incident: submit transitions Draft?Open, default SLA due date (+72h), resolution/closed_on/SLA breach logic.
- SRM Investigation: submit moves linked Open incident to Under Investigation; completion adds incident timeline comment.
- Enabled `allow_on_submit` on lifecycle fields (status, sla_breached, resolution_summary, closed_on).
- Added `test_lifecycle_workflow.py` with 5 lifecycle tests (8 total across app).

### Files changed
- `srm_core/services/__init__.py` (new)
- `srm_core/services/statuses.py` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_investigation/srm_investigation.py` (updated)
- `srm_core/srm_core/doctype/srm_investigation/srm_investigation.json` (updated)
- `srm_core/srm_core/tests/test_lifecycle_workflow.py` (new)
- `docs/CHANGELOG_INTERNAL.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS (8 tests in 0.797s)

### Notes / follow-ups
- SLA breach uses validate-time check only; scheduler deferred.
- Investigation completion comments use `on_update_after_submit` (Frappe update-after-submit path).

