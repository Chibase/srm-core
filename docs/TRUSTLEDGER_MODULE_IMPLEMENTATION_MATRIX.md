# TrustLedger Module Implementation Matrix

> Companion reference to `docs/TRUSTLEDGER_CONSOLIDATED_IMPLEMENTATION_SEQUENCE.md`.
>
> This matrix maps the current SRM modules to their TrustLedger evolution path so implementation can proceed safely, incrementally, and without disturbing current users.

---

## 1. How to use this matrix

For each module, the build path is:
1. preserve the current behavior,
2. enhance it safely,
3. repurpose it where appropriate,
4. add new trust-native support only when needed,
5. validate against the MVP outcome.

This matrix is not a replacement for the charter, roadmap, or process guide. It is the practical mapping layer.

---

## 2. Matrix

| Current module / function area | Safe enhancement | Repurposing direction | New trust additions | MVP outcome |
|---|---|---|---|---|
| Measurement / outcome | add optional trust-oriented fields and helper logic | trust indicators, trust trends, willingness tracking | trust score/state support | measurable trust movement |
| Stakeholder response | add optional sentiment and willingness capture | community feelings, trust barriers, confidence signals | trust observation linkage | richer trust signal capture |
| Evidence | add trust tagging and context support | proof trail for trust claims | trust evidence records | evidence-backed trust reporting |
| Segmentation / geography | add trust-friendly grouping helpers | trust by community, ward, stakeholder group, phase | trust comparison support | trust by place and group |
| AI helper methods | add trust-aware prompt and summary hooks | trust triage, trust response support | recommendation scaffolding | explainable trust assistance |
| Reporting / dashboards | add trust-ready views where possible | trust trend views, proof summaries | trust analytics panels | visible trust insight |
| Notifications / alerts | add trust-related triggers optionally | trust risk alerts, escalation cues | trust alert rules | actionable trust warnings |
| Community context | add optional context fields | local authority and social sensitivity mapping | context record structures | Global South-aware trust handling |
| Release/readiness docs | add trust readiness notes | MVP gap tracking | readiness checklist | defensible MVP posture |

---

## 3. Module priority order

### Priority 1 — Existing modules that can be enhanced safely
- Measurement / outcome
- Stakeholder response
- Evidence
- Segmentation / geography
- AI helper methods

### Priority 2 — Reporting and visibility
- Reporting / dashboards
- Notifications / alerts

### Priority 3 — Context and release support
- Community context
- Release/readiness docs

---

## 4. Implementation rules by module

### Measurement / outcome
- Do not break existing outcome definitions.
- Add trust capability only as optional extension.
- Preserve current calculations and reports.

### Stakeholder response
- Preserve current response capture.
- Add trust, willingness, and confidence as additional dimensions.
- Do not force new fields into every workflow.

### Evidence
- Keep current evidence workflows intact.
- Allow trust claims to point to evidence.
- Preserve verification status behavior.

### Segmentation / geography
- Preserve existing segment meaning.
- Add trust comparison capability without changing segment definitions.

### AI helper methods
- Keep AI advisory.
- Ensure outputs stay explainable.
- Do not allow AI to override evidence or user judgment.

### Reporting / dashboards
- Keep legacy reports available.
- Introduce trust views alongside them.
- Avoid changing default expectations too early.

### Notifications / alerts
- Keep alerts optional and reversible.
- Alert only when trust rules are clearly met.

### Community context
- Prefer optional notes and context structures.
- Do not force a single global interpretation model.

### Release/readiness docs
- Track MVP readiness honestly.
- Keep future scope separate from present capability.

---

## 5. MVP mapping

The platform is closer to MVP when it can:
- measure trust,
- capture trust signals,
- link trust to evidence,
- compare trust across contexts,
- recommend trust actions,
- and present the result in a defensible way.

---

## 6. Approval rule

No module should move to the next phase unless:
- the current behavior is preserved,
- the enhancement is additive,
- tests exist for changed behavior,
- and the product owner approves the shift.
