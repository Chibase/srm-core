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

---

## Packet 05 — Impact Taxonomy + SRM Impact Assessment (2026-07-02)

**Commit:** _(see develop HEAD)_

### Summary
- Added master DocType `SRM Impact Taxonomy` with categories, weights, and active flag.
- Added child-table DocType `SRM Impact Assessment` on SRM Incident (`impact_assessments`).
- Added `srm_core/services/impact.py` helpers (severity ordinal placeholder, duplicate detection, row validation).
- Added idempotent seed patch for four default taxonomies and `SRM Lead` role.
- Added `test_impact_assessment.py` (5 tests; 25 total across app).

### Files changed
- `srm_core/services/impact.py` (new)
- `srm_core/services/permissions.py` (updated)
- `srm_core/patches/v1_0/seed_default_impact_taxonomy.py` (new)
- `srm_core/patches.txt` (updated)
- `srm_core/srm_core/doctype/srm_impact_taxonomy/` (new)
- `srm_core/srm_core/doctype/srm_impact_assessment/` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_impact_assessment.py` (new)
- `srm_core/srm_core/tests/test_helpers.py` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Scoring engine intentionally deferred to Packet 06.
- Impact assessments use child-table pattern (incident link implicit via parent).

---

## Packet 06 — Taxonomy-weighted impact scoring (2026-07-02)

**Commit:** `d2ec019`

### Summary
- Implemented deterministic impact scoring from `impact_assessments` child rows.
- Added read-only incident fields: `impact_score`, `impact_band`, `impact_scored_on`, `impact_scored_by`.
- Extended `srm_core/services/impact.py` with `compute_weighted_score`, `score_to_band`, and severity/weight guards.
- Recompute on every validate; zero-row fallback to score 0 / band Low.
- Added `test_impact_scoring.py` (6 tests; 31 total across app).

### Files changed
- `srm_core/services/impact.py` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_impact_scoring.py` (new)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Dashboard/charts for impact trends deferred to later packet.
- Band thresholds may be recalibrated after stakeholder review.

---

## Packet 07 — Incident Priority Engine + Auto-SLA Targeting (2026-07-02)

**Commit:** `8ff75be`

### Summary
- Added read-only priority fields on SRM Incident: `priority_score`, `priority_level`, `priority_computed_on`, `priority_computed_by`.
- Added SLA targeting fields: `sla_target_hours`, `sla_due_by` (synced to `sla_due_date` for breach logic).
- Created `srm_core/services/priority.py` with deterministic 70/30 impact/sentiment blend and quartile P4–P1 bands.
- Sentiment resolution prefers `linked_incident`; falls back to same geographic area within 30 days.
- SLA due from creation on first compute; recomputes from now when priority changes pre-closure; frozen when Closed.
- Idempotent backfill patch for existing incidents.
- Added `test_priority_engine.py` (6 tests; 37 total across app).

### Files changed
- `srm_core/services/priority.py` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_priority_engine.py` (new)
- `srm_core/patches/v1_0/backfill_incident_priority_sla.py` (new)
- `srm_core/patches.txt` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Sentiment fallback window (30 days) may be tuned after operational review.
- Dashboard priority/SLA views deferred to later packet.

---

## Packet 08 — Investigation Tasking + Assignment Workflow (2026-07-02)

**Commit:** `5372bee`

### Summary
- Added child-table DocType `SRM Investigation Task` with assignee, status flow, due date, and completion tracking.
- Added `investigation_tasks` table on SRM Incident with validation for required fields, Done timestamps, duplicate open tasks, and past due dates on new rows.
- Close-gate blocks Closed status when blocking tasks exist unless user has System Manager role.
- Created `srm_core/services/investigation_tasks.py` with duplicate detection, blocking-task summarizer, and status transition helpers.
- Added SRM Lead write permission on Incident for task management via parent edit.
- Added `test_investigation_tasks.py` (9 tests; 46 total across app).

### Files changed
- `srm_core/services/investigation_tasks.py` (new)
- `srm_core/services/permissions.py` (updated)
- `srm_core/srm_core/doctype/srm_investigation_task/` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_investigation_tasks.py` (new)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Task notifications/email automation deferred to later packet.
- Assignee workload views deferred to later packet.

---

## Packet 09 — Escalation Rules + Assignment Enforcement (2026-07-02)

**Commit:** `9ff3cf9`

### Summary
- Added read-only escalation fields on SRM Incident: `is_escalated`, `escalation_level`, `escalated_on`, `escalated_by`, plus editable `requires_executive_attention` and `escalation_reason`.
- Added `incident_owner` (Link User) for assignment accountability.
- Created `srm_core/services/escalation.py` with deterministic L1–L3 derivation, `[AUTO]` reason handling, and P1/P2 assignment enforcement.
- Escalation computed after priority/SLA logic; SLA breach included in L2 path.
- Idempotent backfill patch for existing incidents.
- Added `test_escalation_rules.py` (10 tests; 56 total across app).

### Files changed
- `srm_core/services/escalation.py` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_escalation_rules.py` (new)
- `srm_core/patches/v1_0/backfill_incident_escalation.py` (new)
- `srm_core/patches.txt` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Escalation notifications/webhooks deferred to later packet.
- Existing P1/P2 incidents may need owner/task assignment on next edit.

---

## Packet 10 — Incident Timeline Events (2026-07-02)

**Commit:** `a0b3318`

### Summary
- Added append-only DocType `SRM Incident Event` with indexed incident/event_time, structured `details_json`, severity, and unique `idempotency_key`.
- Created `srm_core/services/timeline.py` with event builders, diff helpers, emission, and `get_incident_timeline()`.
- Hooked SRM Incident `after_insert`/`on_update`/`on_submit` to emit events on actual field/task diffs only.
- Idempotent backfill patch creates baseline `INCIDENT_CREATED` and status snapshot events for existing incidents.
- Added `test_incident_timeline.py` (9 tests; 65 total across app).

### Files changed
- `srm_core/services/timeline.py` (new)
- `srm_core/srm_core/doctype/srm_incident_event/` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_incident_timeline.py` (new)
- `srm_core/patches/v1_0/backfill_incident_timeline.py` (new)
- `srm_core/patches.txt` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Timeline UI page deferred to later packet.
- REST endpoint wrapper for `get_incident_timeline()` deferred.

---

## Packet 11 — Notification Rules Engine (2026-07-02)

**Commit:** `2d51c9b`

### Summary
- Added standalone DocType `SRM Notification` with queued/sent/failed lifecycle, idempotency keys, and in-app read tracking.
- Created `srm_core/services/notifications.py` with rule evaluation, queueing, stub dispatch, and read helpers.
- Initial rules: escalation L2/L3, SLA due within 6h, status Closed, priority P1-Critical.
- Hooked notification processing into timeline `emit_incident_event()` after each new event.
- Idempotent bootstrap patch for recent P1/P2 open incidents.
- Added `test_notifications.py` (10 tests; 75 total across app).

### Files changed
- `srm_core/services/notifications.py` (new)
- `srm_core/services/permissions.py` (updated)
- `srm_core/services/timeline.py` (updated)
- `srm_core/srm_core/doctype/srm_notification/` (new)
- `srm_core/srm_core/tests/test_notifications.py` (new)
- `srm_core/patches/v1_0/backfill_high_priority_notifications.py` (new)
- `srm_core/patches.txt` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Real SMTP/provider integration deferred; stub dispatch marks email sent when address exists.
- Notification desk UI deferred to later packet.

---

## Packet 12 — Incident Commenting + Mention Notifications (2026-07-02)

**Commit:** `4d37b67`

### Summary
- Added child-table DocType `SRM Incident Comment` with audit stamps, internal flag, and CSV `mention_users`.
- Added `comments` table on SRM Incident with plain-text `@mention` parsing and validation.
- Integrated `COMMENT_ADDED` timeline events with structured payload (comment id, internal flag, mention count).
- Extended notification rules with `comment_mention` fan-out (deduped, no self-notify, unresolved mentions ignored).
- Added `get_incident_comments()` read helper and `test_incident_comments.py` (10 tests; 85 total across app).

### Files changed
- `srm_core/services/comments.py` (new)
- `srm_core/services/timeline.py` (updated)
- `srm_core/services/notifications.py` (updated)
- `srm_core/srm_core/doctype/srm_incident_comment/` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/tests/test_incident_comments.py` (new)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Rich-text editor deferred; plain text only.
- Comment edit does not re-notify newly added mentions (add-only fan-out).

---

## Packet 13 — Incident Attachment Registry + Evidence Controls (2026-07-02)

**Commit:** `0fdc3fc`

### Summary
- Added child-table DocType `SRM Incident Attachment` with classification, integrity hash, primary flag, and soft-remove audit fields.
- Added `attachments` table on SRM Incident with validation, single active primary evidence rule, and closed-incident guardrails.
- Created `srm_core/services/attachments.py` with integrity hash helper and read API.
- Extended timeline with `ATTACHMENT_ADDED` / `ATTACHMENT_REMOVED` events and `sensitive_evidence_added` notifications for confidential/restricted uploads.
- Added `test_incident_attachments.py` (11 tests; 96 total across app).

### Files changed
- `srm_core/services/attachments.py` (new)
- `srm_core/services/timeline.py` (updated)
- `srm_core/services/notifications.py` (updated)
- `srm_core/srm_core/doctype/srm_incident_attachment/` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/doctype/srm_incident_event/srm_incident_event.json` (updated)
- `srm_core/srm_core/tests/test_incident_attachments.py` (new)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Binary hash population from File content deferred (helper accepts bytes when available).
- External object storage integration deferred.

---

## Packet 14 — Risk Register Auto-Linking + Residual Risk Rollup (2026-07-02)

**Commit:** _(see develop HEAD)_

### Summary
- Added minimal `SRM Risk Register` DocType (link target only; no redesign) with `incident_references` touchpoint field.
- Added incident risk link fields (`linked_risk`, link audit stamps, residual score/band/rationale).
- Created `srm_core/services/risk_rollup.py` with deterministic residual scoring, close-gate validation, and best-effort risk register reference updates.
- Extended timeline with `RISK_LINKED` / `RESIDUAL_RISK_UPDATED` events and notification rules `risk_linked` / `residual_risk_critical`.
- Added idempotent backfill patch for incidents with existing `linked_risk` and `test_risk_rollup.py` (14 tests; 110 total across app).

### Files changed
- `srm_core/services/risk_rollup.py` (new)
- `srm_core/services/timeline.py` (updated)
- `srm_core/services/notifications.py` (updated)
- `srm_core/srm_core/doctype/srm_risk_register/` (new)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.json` (updated)
- `srm_core/srm_core/doctype/srm_incident/srm_incident.py` (updated)
- `srm_core/srm_core/doctype/srm_incident_event/srm_incident_event.json` (updated)
- `srm_core/patches/v1_0/backfill_incident_residual_risk.py` (new)
- `srm_core/patches.txt` (updated)
- `srm_core/srm_core/tests/test_risk_rollup.py` (new)
- `srm_core/srm_core/tests/test_helpers.py` (updated)
- `docs/CHANGELOG_INTERNAL.md` (updated)
- `docs/DECISIONS.md` (updated)

### Migration / tests
- migrate: PASS
- run-tests: PASS

### Notes / follow-ups
- Risk register UI/workflow expansion deferred; current DocType is minimal link target.
- Residual recompute on every validate when linked; batch recompute job deferred.

