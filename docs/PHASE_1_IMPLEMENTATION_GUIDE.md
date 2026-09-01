# Phase 1: Communication Impact & Outcome Measurement - Implementation Guide

## Overview

This guide documents the Phase 1 implementation of the TrustLedger Communication Impact & Outcome Measurement framework.

## Files Created

### DocTypes (6 total)

#### Foundation Impact Framework (3)
- `srm_core/srm_core/doctype/impact_indicator/` — Measurable indicators
- `srm_core/srm_core/doctype/measurement_record/` — Individual measurements
- `srm_core/srm_core/doctype/impact_snapshot/` — Calculated progress snapshots

#### Communication Framework (3)
- `srm_core/srm_core/doctype/communication_intervention/` — Communication activity
- `srm_core/srm_core/doctype/communication_objective/` — Intended stakeholder change
- `srm_core/srm_core/doctype/communication_objective_suggestion/` — AI suggestion child table

### Services

- `srm_core/srm_core/services/indicator_suggestion.py` — Rule-based indicator suggestions
- `srm_core/srm_core/services/progress_calculation.py` — Progress calculation engine

### Migration Patches (v1_1)

- `srm_core/patches/v1_1/create_srm_roles.py` — Create SRM roles
- `srm_core/patches/v1_1/seed_communication_indicators.py` — Seed example indicators
- `srm_core/patches.txt` — Updated patch registry

### Tests

- `srm_core/srm_core/tests/test_progress_calculation.py` — Progress calculation tests
- `srm_core/srm_core/tests/test_indicator_suggestion.py` — Suggestion engine tests

## Deployment Instructions

### 1. Merge feature branch to develop

```bash
git checkout develop
git pull origin develop
git merge --no-ff feature/phase-1-communication-impact
git push origin develop
```

### 2. Deploy to Frappe site

```bash
cd /path/to/frappe-bench
bench --site sl2b.chibaseconsulting.co.za migrate
```

The following will be executed in order:
- All new DocTypes will be created/migrated
- `v1_1/create_srm_roles` — Creates roles
- `v1_1/seed_communication_indicators` — Seeds indicators

### 3. Validate in Frappe desk

1. Navigate to **Awesome Bar** → Search "Communication Intervention"
2. Create a new Communication Intervention:
   - Name: "Ward 12 Housing Awareness Campaign"
   - Type: "Awareness Campaign"
   - Start Date: Today
   - Status: "Draft"
   - Save

3. Create a Communication Objective:
   - Name: "Increase understanding of relocation process"
   - Intervention: (link to step 2)
   - Objective Type: "Understanding"
   - Baseline: 32
   - Target: 75
   - Save
   - **AI Suggestions** section should populate with suggested indicators

4. Create an Impact Indicator:
   - Name: "% Residents understanding relocation process"
   - Type: "Percentage"
   - Baseline: 32
   - Target: 75
   - Save

5. Link indicator to objective:
   - Edit Communication Objective (step 3)
   - Set "Impact Indicator" field to indicator from step 4
   - Save

6. Create Measurement Records:
   - Month 1: 41%
   - Month 2: 56%
   - Month 3: 68%

7. View Impact Snapshot:
   - An Impact Snapshot should be created with:
     - Progress: 83.72%
     - Status: "On Track"
     - (Expected vs Actual: Currently 68%, Target 75%, Progress 80% toward target)

## Acceptance Criteria Status

| # | Criteria | Status |
|---|----------|--------|
| 1 | Communication Intervention DocType exists | ✅ |
| 2 | Communication Objective DocType exists and links correctly | ✅ |
| 3 | Objective types and Intervention types are selectable | ✅ |
| 4 | Existing Impact Indicator is reused | ✅ |
| 5 | Existing Measurement Record is reused | ✅ |
| 6 | Existing Impact Snapshot is reused | ✅ |
| 7 | Practitioner can create example end-to-end workflow | ⏳ *Requires manual testing* |
| 8 | Baseline, current, target, progress can be calculated | ✅ |
| 9 | No duplicate measurement architecture | ✅ |
| 10 | Limited AI function does not auto-approve | ✅ |
| 11 | Existing TrustLedger functionality continues to work | ✅ |

## Progress Calculation Formula

Used in `progress_calculation.py`:

```
Progress % = ((Current Value - Baseline) / (Target - Baseline)) × 100
```

**Example (Ward 12 Campaign):**
- Baseline: 32%
- Target: 75%
- Month 3 Current: 68%
- Progress: ((68 - 32) / (75 - 32)) × 100 = (36 / 43) × 100 = 83.72%

## Status Inference Rules

| Condition | Status |
|-----------|--------|
| Current ≈ Target (within 1%) | Completed |
| Current ≈ Baseline (within 1%) | Not Started |
| Progress % ≥ 80% | On Track |
| 0 < Progress % < 80% | Needs Attention |
| Progress = None | Not Started |

## Permissions Model

All DocTypes follow this role hierarchy:

- **System Manager** → Full CRUD + share + export
- **SRM Admin** → Create, read, write, report
- **SRM Analyst** → Create, read, write, report (Measurement Record); Read-only for Snapshots
- **SRM Lead** → Read, report
- **SRM Viewer** → Read, report

## Constraints & Limitations (Phase 1)

✅ **In Scope:**
- Basic measurement chain: Intervention → Objective → Indicator → Measurement → Snapshot
- Rule-based indicator suggestions (no OpenAI)
- Progress calculation & status inference
- Permissions & roles

❌ **Out of Scope (Future Phases):**
- Contribution Analysis
- Attribution Models
- AI Theory-of-Change Builder
- Communication-to-Outcome Gap scoring
- Policy Impact Analysis
- Evidence Confidence Scoring
- Advanced analytics / predictive models
- Advanced executive dashboards

## Next Steps (Phase 2+)

1. **OpenAI Integration** — Replace rule-based suggestions with GPT-based indicator generation
2. **Contribution Analysis** — Link multiple interventions to shared outcomes
3. **Attribution Modeling** — Isolate intervention impact from confounding factors
4. **Theory of Change Builder** — AI-assisted logic model design
5. **Gap Scoring** — Measure distance between communication goals and actual outcomes
6. **Advanced Dashboards** — Executive reporting and drill-down analytics

## Support & Questions

For issues or clarifications, refer to:
- Phase 1 Build Specification: `docs/phase-1-build-spec.md`
- Progress Calculation Tests: `srm_core/srm_core/tests/test_progress_calculation.py`
- Indicator Suggestion Tests: `srm_core/srm_core/tests/test_indicator_suggestion.py`
