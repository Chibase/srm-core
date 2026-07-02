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

