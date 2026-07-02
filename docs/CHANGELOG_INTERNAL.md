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

---

## Packet 03 — Permissions baseline and IKS guardrails (2026-07-02)

**Commit:** _(see develop HEAD)_

### Summary
- Added custom roles: SRM Admin, SRM Case Manager, SRM Analyst, SRM Viewer (patch + helper).
- Applied role-based DocType permissions on SRM Incident, SRM Investigation, SRM Sentiment Capture.
- Preserved System Manager full access on all three DocTypes.
- Added IKS guardrails on SRM Incident (close/resolution_summary restrictions, audit fields).
- Added `test_iks_permissions.py` with 6 tests (14 total across app).

### Files changed
- `srm_core/services/permissions.py` (new)
- `srm_core/patches/v1_0/create_srm_roles.py` (new)
- `srm_core/patches.txt` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_investigation/srm_investigation.json` (updated)
- `srm_core/srm_core/doctype/srm_sentiment_capture/srm_sentiment_capture.json` (updated)
- `srm_core/srm_core/tests/test_iks_permissions.py` (new)
- `srm_core/srm_core/tests/test_core_doctypes.py` (updated)
- `srm_core/srm_core/tests/test_lifecycle_workflow.py` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS (14 tests in 2.086s)

### Notes / follow-ups
- IKS close guard applies when transitioning to Closed, not on every save while already closed.
- Role-permission enforcement at desk layer; server-side IKS checks are additive guardrails.

---

## Packet 04 — Geographic Area foundation and linkage migration (2026-07-02)

**Commit:** _(see develop HEAD)_

### Summary
- Added tree DocType `Geographic Area` with nested-set hierarchy and role permissions.
- Linked `geographic_area` on SRM Incident and SRM Sentiment Capture; retained hidden legacy `geographic_area_text`.
- Added idempotent patch to create/backfill Geographic Area links from legacy text.
- Added server-side validation requiring linked geographic area on Incident/Sentiment.
- Added `test_geographic_area_migration.py` (6 tests; 20 total across app).

### Files changed
- `srm_core/srm_core/doctype/geographic_area/` (new)
- `srm_core/services/geographic_area.py` (new)
- `srm_core/patches/v1_0/migrate_geographic_area_links.py` (new)
- `srm_core/patches.txt` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/doctype/srm_sentiment_capture/srm_sentiment_capture.json` (updated)
- `srm_core/srm_core/doctype/srm_sentiment_capture/srm_sentiment_capture.py` (updated)
- `srm_core/srm_core/tests/test_geographic_area_migration.py` (new)
- `srm_core/srm_core/tests/test_helpers.py` (new)
- `srm_core/srm_core/tests/test_core_doctypes.py` (updated)
- `srm_core/srm_core/tests/test_lifecycle_workflow.py` (updated)
- `srm_core/srm_core/tests/test_iks_permissions.py` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Legacy `geographic_area_text` planned for removal in a future packet (see ADR-003).
- Patch logs created/linked counts to `srm_core` logger on migrate.

