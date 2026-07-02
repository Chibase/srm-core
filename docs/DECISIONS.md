# SRM Core ??? Architecture Decision Log

Record significant technical and product decisions here. One entry per decision.

---

## Template

Copy this block for each new decision:

```markdown
### ADR-NNN: <Short title>

- **Date:** YYYY-MM-DD
- **Status:** Proposed | Accepted | Superseded | Deprecated
- **Context:** What problem or choice prompted this decision?
- **Decision:** What was decided?
- **Consequences:** What becomes easier or harder as a result?
- **Alternatives considered:** What else was evaluated?
```

---

## Decisions

### ADR-001: Frappe DocType-first domain model

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** SRM Core needs persistent entities (stakeholders, engagements, geography) with permissions, audit trail, and desk UX.
- **Decision:** Model all domain entities as Frappe DocTypes within the `srm_core` app rather than external databases or custom ORM layers.
- **Consequences:** Faster delivery using Frappe desk, permissions, and reporting; tied to Frappe upgrade cycle.
- **Alternatives considered:** Standalone API + PostgreSQL service; extending ERPNext CRM Contact/Lead only.

### ADR-002: Packet-driven implementation on `develop`

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Need traceable, reviewable increments with clear scope boundaries.
- **Decision:** Deliver via numbered packets (see `BUILD_PLAN.md`); one packet = one commit; agents implement only the active packet.
- **Consequences:** Predictable diffs and changelog; requires discipline to avoid scope creep.
- **Alternatives considered:** Feature branches per epic without packet numbering; monolithic initial release.

### ADR-003: Retain legacy `geographic_area_text` during Geographic Area migration

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Incident and Sentiment Capture initially stored geography in free-text `geographic_area_text` fields before the Geographic Area master existed.
- **Decision:** Introduce Link field `geographic_area` (required for new/edited docs), keep `geographic_area_text` hidden and read-only for legacy visibility, and backfill links via idempotent patch. Planned removal of `geographic_area_text` in a future packet after migration verification.
- **Consequences:** Safer rollout with backward-compatible data; temporary schema duplication until legacy field removal.
- **Alternatives considered:** Immediate deletion of text field (risky for unmigrated rows); permanent dual-entry by users (inconsistent data).

### ADR-004: Taxonomy-driven impact model before scoring engine

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Incident impact needs structured, configurable dimensions before a composite risk score can be calculated.
- **Decision:** Introduce `SRM Impact Taxonomy` master data and embed `SRM Impact Assessment` rows on incidents via a child table; defer scoring math to Packet 06 with ordinal placeholders in `srm_core/services/impact.py`.
- **Consequences:** Users can capture consistent impact lines per incident now; scoring can layer on without schema churn later.
- **Alternatives considered:** Standalone assessment DocType with dashboard links only (more clicks, weaker form UX); hard-coded severity dimensions (inflexible).

### ADR-005: Weighted normalization and quartile impact bands

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Packet 06 requires a deterministic composite impact score from heterogeneous taxonomy rows with different weights and ordinal severities.
- **Decision:** Compute `normalized_score_0_100 = (Σ(severity×weight) / (Σ(weight)×5)) × 100`, round to 2 decimals, and map bands at quartile thresholds (Low <25, Moderate <50, High <75, Critical ≥75).
- **Consequences:** Scores stay comparable across incidents with different taxonomy mixes; band cutoffs are simple to explain pending calibration with stakeholders.
- **Alternatives considered:** Simple average of severities (ignores taxonomy weights); fixed weighted sum without normalization (unbounded scale).

### ADR-006: Impact-sentiment priority blend and SLA recompute policy

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Packet 07 needs a deterministic incident priority derived from impact score (Packet 06) plus community sentiment, with auto SLA targets tied to priority bands.
- **Decision:** Compute `priority_score = min(100, round(impact_score×0.70 + sentiment_contrib, 2))` where `sentiment_contrib = (abs(clamp(sentiment_score,-100..100))/100)×30`. Map P4–P1 at the same quartile cutoffs as impact bands. Resolve sentiment via `SRM Sentiment Capture.linked_incident` when present; otherwise latest capture in the same `geographic_area` within 30 days of incident creation (fallback). Set `sla_due_by` from incident `creation` on first compute; when `priority_level` changes before closure, recompute from current timestamp; freeze `sla_due_by` once status is Closed. Mirror `sla_due_by` to legacy `sla_due_date` for breach checks.
- **Consequences:** Priority and SLA stay explainable and testable; sentiment linkage quality affects accuracy until direct links are populated.
- **Alternatives considered:** Equal 50/50 impact/sentiment weighting; never recomputing SLA after create (stale targets after escalation).

### ADR-007: Close-gate tied to unresolved investigation tasks

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Packet 08 introduces structured investigation tasks on incidents; closing while tasks remain Open/In Progress/Blocked risks losing accountability for follow-up work.
- **Decision:** Block transition to Closed when any investigation task is in Open, In Progress, or Blocked status. Validation lists up to five blocking task titles plus an overflow suffix. System Manager may override and close anyway.
- **Consequences:** Closure quality improves; operators must complete or cancel tasks (or escalate to System Manager) before routine close.
- **Alternatives considered:** Soft warnings only (ignored in practice); separate task DocType with no close coupling (weaker enforcement).

### ADR-008: Escalation precedence, auto-reason policy, and assignment enforcement

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Packet 09 needs deterministic escalation tied to priority, impact, SLA breach, and executive-attention signals, plus accountability for high-priority incidents.
- **Decision:** Derive escalation level with highest-wins precedence (L3: P1-Critical, Critical impact band, or executive-attention flag; L2: P2-High or SLA breach; L1: P3-Medium). Auto-generate escalation reasons with `[AUTO]` prefix when blank; preserve manual reasons. Keep historical `escalated_on`/`escalated_by` on de-escalation; refresh stamps on first escalate or level increase. Use canonical `incident_owner` (Link User) for ownership; require owner plus at least one assigned investigation task for P1/P2 incidents.
- **Consequences:** Escalation state is auditable and explainable; high-priority incidents cannot be saved without clear ownership and task assignment.
- **Alternatives considered:** Separate Escalation DocType (more overhead); owner inferred from Frappe document owner field (less explicit for reassignment).

### ADR-009: Append-only incident timeline with idempotency keys

- **Date:** 2026-07-02
- **Status:** Accepted
- **Context:** Packet 10 needs an immutable audit trail of incident state transitions (score, priority, escalation, SLA, tasks, lifecycle) queryable without coupling to the mutable incident document.
- **Decision:** Introduce standalone append-only `SRM Incident Event` rows inserted only by system code (`ignore_permissions` + DocType guards). Emit events on actual diffs after save via `after_insert`/`on_update` hooks; use deterministic SHA256-based `idempotency_key` per incident + event type + transition snapshot to suppress duplicates on no-op saves. Provide `get_incident_timeline()` server helper (permission check left to caller).
- **Consequences:** Timeline is query-friendly and safe to backfill; event volume stays bounded on repeated saves.
- **Alternatives considered:** Embedded JSON log on Incident (harder to query); Comment doctype reuse (weak structure and permissions).

