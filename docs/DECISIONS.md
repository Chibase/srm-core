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

