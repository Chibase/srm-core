# Phase 2: Outcome Measurement & Dashboard - Implementation Guide

## Overview

Phase 2 extends Phase 1 to add comprehensive outcome measurement, progress tracking, and basic dashboarding capabilities. No new DocTypes are created; all Phase 2 features leverage Phase 1's Communication Intervention, Communication Objective, Impact Indicator, Measurement Record, and Impact Snapshot.

**Phase 2 Focus:** Prove the measurement engine works. Practitioners should be able to:
1. Open an intervention
2. See all linked objectives and their outcome types
3. See baseline → current → target for each
4. See progress % and simple status
5. See trend of measurements over time

## Architecture

### Data Flow (No New DocTypes)

```
Communication Intervention
  ↓ (has many)
Communication Objective (outcome_type: Awareness|Understanding|Trust|Participation|Behaviour Change|Service Uptake)
  ↓ (links to)
Impact Indicator
  ↓ (measured by)
Measurement Record (baseline → Month 1 → Month 2 → Month 3 → ...)
  ↓ (generates)
Impact Snapshot (calculated progress %, status)
```

### New Backend Services

#### 1. `outcome_measurement.py`
**Responsibility:** Record and retrieve measurements by outcome type.

**Key Functions:**
- `get_outcome_type_info(type)` → Returns metadata for outcome type
- `validate_outcome_type(type)` → Validates outcome type
- `measure_outcome(...)` → Records a measurement for an outcome
- `get_outcome_measurements(objective_name)` → Fetch all measurements
- `get_baseline_current_target(objective_name)` → Get baseline, current, target

**Supported Outcome Types:**
- Awareness — % of target audience aware
- Understanding — % who understand concepts
- Trust — Trust score/rating
- Participation — % participation or count engaged
- Behaviour Change — % demonstrating new behavior
- Service Uptake — % utilizing service

#### 2. `outcome_progress_tracker.py`
**Responsibility:** Track progress and infer status.

**Key Functions:**
- `get_outcome_progress(objective_name)` → Current progress data with status
- `get_outcome_trend(objective_name)` → Historical measurement trend
- `get_intervention_outcome_summary(intervention_name)` → Aggregate all objectives
- `get_dashboard_data()` → All interventions summary

**Status Inference:**
- `On Track` — Progress ≥ 80% toward target
- `Needs Attention` — Progress between 0-80%
- `Off Track` — Current value < baseline (regression)
- `No Data` — No measurements recorded

#### 3. `dashboard_api.py`
**Responsibility:** Expose outcome data via REST API.

**Endpoints:**
- `GET /api/method/srm_core.services.dashboard_api.get_intervention_dashboard?intervention_name=[name]`
- `GET /api/method/srm_core.services.dashboard_api.get_outcome_trend_api?objective_name=[name]`
- `GET /api/method/srm_core.services.dashboard_api.get_objective_progress?objective_name=[name]`
- `GET /api/method/srm_core.services.dashboard_api.get_all_interventions_summary`

## Deployment

### 1. Merge to develop
```bash
git checkout develop
git pull origin develop
git merge --no-ff feature/phase-2-outcome-measurement
git push origin develop
```

### 2. Deploy to Frappe
```bash
bench --site sl2b.chibaseconsulting.co.za migrate
```

No new DocTypes to migrate. Phase 2 patches are no-ops (future-proofing).

### 3. Verify API endpoints
```bash
# Intervention dashboard
curl http://localhost:8000/api/method/srm_core.services.dashboard_api.get_intervention_dashboard?intervention_name=Ward%2012%20Housing%20Awareness%20Campaign

# Objective progress
curl http://localhost:8000/api/method/srm_core.services.dashboard_api.get_objective_progress?objective_name=Increase%20residents%27%20understanding%20of%20relocation%20process

# Trend data
curl http://localhost:8000/api/method/srm_core.services.dashboard_api.get_outcome_trend_api?objective_name=Increase%20residents%27%20understanding%20of%20relocation%20process

# All interventions
curl http://localhost:8000/api/method/srm_core.services.dashboard_api.get_all_interventions_summary
```

## Phase 2 User Journey

### Example: Ward 12 Housing Awareness Campaign

**Step 1: Practitioner opens intervention detail page**

```
Ward 12 Housing Awareness Campaign
Status: Active
Start Date: 2026-08-01
```

**Step 2: Sees all objectives with outcome types**

```
OBJECTIVES:

┌─────────────────────────────────────────────────┐
│ Increase residents' understanding of relocation │
│ Type: UNDERSTANDING                             │
│ Baseline: 32% → Current: 68% → Target: 75%     │
│ Progress: 83.72%  Status: ✅ ON TRACK          │
└─────────────────────────────────────────────────┘
```

**Step 3: Sees measurement trend**

```
TREND OVER TIME:

32% (Baseline)
  ↓ (+9%)
41% (Month 1)
  ↓ (+15%)
56% (Month 2)
  ↓ (+12%)
68% (Month 3, Current)
  ↓ (+7% needed)
75% (Target)
```

**Step 4: Sees overall intervention progress**

```
OVERALL PROGRESS

Awareness         78% ✅ On Track
Understanding     83% ✅ On Track
Trust             62% ⚠️  Needs Attention
Participation     55% ⚠️  Needs Attention
Behaviour         48% ⚠️  Needs Attention
Service Uptake    43% ⚠️  Needs Attention

Average Progress: 61%
```

**Step 5: Records new measurement**

```
[Form]
Outcome Type: Understanding
Date: 2026-09-01
Measured Value: 71%
[Save]
```

**Step 6: Snapshot updates automatically**

```
UNDERSTANDING PROGRESS UPDATE

Baseline: 32%
Current: 71% (was 68%)
Target: 75%

Progress: 87.21% (was 83.72%)
Status: ✅ ON TRACK
Trend: ↗ Moving up (+3%)
```

## Frontend Components to Build (Phase 2)

### 1. Intervention Detail Page
**Component:** `InterventionDetailView.tsx`

**Shows:**
- Intervention name, type, dates, status
- List of linked objectives (by outcome type)
- For each objective:
  - Outcome type badge
  - Baseline → Current → Target
  - Progress % with color-coded bar
  - Status badge
  - Button to view trend / record measurement

**Data Source:**
```typescript
GET /api/method/srm_core.services.dashboard_api.get_intervention_dashboard
  ?intervention_name=[name]
```

### 2. Outcome Dashboard
**Component:** `OutcomeDashboard.tsx`

**Shows:**
- Grid/table of all interventions
- For each intervention:
  - Name + status badge
  - Overall progress %
  - Breakdown by outcome type (6 rows max)
  - Link to detail view
- Summary cards:
  - Total interventions
  - Avg progress %
  - % on track

**Data Source:**
```typescript
GET /api/method/srm_core.services.dashboard_api.get_all_interventions_summary
```

### 3. Trend Visualization
**Component:** `TrendChart.tsx`

**Shows:**
- Line chart or sparkline
- X-axis: Measurement dates (or periods: Baseline, M1, M2, M3, ...)
- Y-axis: Measurement values
- Baseline marked with different color/style
- Target marked as horizontal line
- Current point highlighted
- Tooltip showing value + date on hover

**Data Source:**
```typescript
GET /api/method/srm_core.services.dashboard_api.get_outcome_trend_api
  ?objective_name=[name]
```

### 4. Outcome Progress Card
**Component:** `OutcomeProgressCard.tsx`

**Shows:**
- Outcome type (Awareness, Understanding, etc)
- Baseline | Current | Target (three numbers)
- Progress bar (visual)
- Progress % (number)
- Status badge with color:
  - Green: On Track
  - Yellow: Needs Attention
  - Red: Off Track
  - Gray: No Data

**Props:**
```typescript
interface OutcomeProgressCardProps {
  objectiveName: string;
  outcomeType: 'Awareness' | 'Understanding' | 'Trust' | ...;
  baseline: number;
  current: number;
  target: number;
  progressPct: number;
  status: 'On Track' | 'Needs Attention' | 'Off Track' | 'No Data';
  measurementsCount: number;
}
```

### 5. Measurement Recording Form
**Component:** `RecordMeasurementForm.tsx`

**Shows:**
- Outcome type (pre-filled or selected)
- Date picker (default today)
- Value input (number)
- Notes textarea (optional)
- Save button
- On success: toast + refresh parent

**Action:**
```typescript
POST /api/resource/Measurement Record
{
  "impact_indicator": "[indicator_name]",
  "measurement_date": "2026-09-01",
  "measured_value": 71,
  "notes": "Understanding outcome measurement"
}
```

## Service Layer Updates (Frontend)

### Add to `communicationImpactService.ts`

```typescript
// Outcome progress
async getOutcomeProgress(objectiveName: string): Promise<OutcomeProgress> {
  return this.get(
    `/api/method/srm_core.services.dashboard_api.get_objective_progress`,
    { objective_name: objectiveName }
  );
}

// Intervention dashboard
async getInterventionDashboard(interventionName: string): Promise<InterventionDashboard> {
  return this.get(
    `/api/method/srm_core.services.dashboard_api.get_intervention_dashboard`,
    { intervention_name: interventionName }
  );
}

// Outcome trend
async getOutcomeTrend(objectiveName: string): Promise<OutcomeTrend> {
  return this.get(
    `/api/method/srm_core.services.dashboard_api.get_outcome_trend_api`,
    { objective_name: objectiveName }
  );
}

// All interventions
async getAllInterventionsSummary(): Promise<DashboardSummary> {
  return this.get(
    `/api/method/srm_core.services.dashboard_api.get_all_interventions_summary`
  );
}
```

## Type Definitions (Frontend)

### Add to `types/communicationImpact.ts`

```typescript
export type OutcomeType = 
  | 'Awareness'
  | 'Understanding'
  | 'Trust'
  | 'Participation'
  | 'Behaviour Change'
  | 'Service Uptake';

export type OutcomeStatus = 
  | 'On Track'
  | 'Needs Attention'
  | 'Off Track'
  | 'No Data';

export interface OutcomeProgress {
  objective_name: string;
  outcome_type: OutcomeType;
  baseline: number;
  current: number;
  target: number;
  progress_pct: number;
  status: OutcomeStatus;
  status_color: string;  // hex color
  last_measurement_date: string | null;
  measurements_count: number;
}

export interface OutcomeTrend {
  baseline: number;
  measurements: Array<{
    date: string;
    value: number;
  }>;
  target: number;
}

export interface InterventionDashboard {
  intervention_name: string;
  overall_progress_pct: number | null;
  outcomes: Record<OutcomeType, OutcomeProgress>;
  total_objectives: number;
  objectives_on_track: number;
  last_updated: string;
}

export interface DashboardSummary {
  interventions: InterventionDashboard[];
  summary: {
    total_interventions: number;
    avg_progress: number | null;
  };
  last_updated: string;
}
```

## Testing Checklist

### Backend Tests (Already Complete)
- ✅ `test_outcome_measurement.py` (6 scenarios)
- ✅ `test_outcome_progress_tracker.py` (4 scenarios)

**Run:**
```bash
python -m pytest srm_core/srm_core/tests/test_outcome_measurement.py -v
python -m pytest srm_core/srm_core/tests/test_outcome_progress_tracker.py -v
```

### API Endpoint Tests (Cursor)
- [ ] GET intervention dashboard returns correct structure
- [ ] GET outcome progress calculates correctly
- [ ] GET outcome trend shows measurements in order
- [ ] GET all interventions summary aggregates correctly

### Frontend Component Tests (Cursor)
- [ ] InterventionDetailView loads and displays objectives
- [ ] Outcome cards show correct progress % and status
- [ ] Trend chart displays measurements
- [ ] Measurement form submits and refreshes data
- [ ] Dashboard shows all interventions
- [ ] Status badges have correct colors
- [ ] Mobile responsive

### End-to-End Test (Ward 12 Workflow)
- [ ] Intervention page loads
- [ ] All 6 objectives visible (one per outcome type)
- [ ] Each shows baseline → current → target
- [ ] Each shows progress % and status
- [ ] Each shows trend visualization
- [ ] Can record new measurement
- [ ] Snapshot updates automatically
- [ ] Overall intervention progress recalculates
- [ ] Dashboard summary updates

## Acceptance Criteria (Phase 2)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Outcome Measurement service implemented | ✅ |
| 2 | Progress Tracker service implemented | ✅ |
| 3 | Dashboard API endpoints functional | ✅ |
| 4 | Outcome status inference (On Track/Needs Attention/Off Track/No Data) | ✅ |
| 5 | Baseline → Current → Target display works | 📋 Frontend |
| 6 | Progress % calculation correct | ✅ |
| 7 | Trend visualization implemented | 📋 Frontend |
| 8 | Intervention dashboard shows all outcome types | 📋 Frontend |
| 9 | Measurement recording updates snapshot | ✅ |
| 10 | End-to-end Ward 12 workflow functional | 📋 Frontend |
| 11 | Mobile responsive | 📋 Frontend |
| 12 | No breaking changes to Phase 1 | ✅ |

## What's NOT in Phase 2 (Saved for Phase 3+)

❌ **Out of Scope:**
- AI-generated analysis or narrative
- Attribution modeling (isolating intervention impact)
- Contribution analysis (multiple interventions → shared outcome)
- Causal inference or impact estimation
- Evidence confidence scoring
- Predictive analytics or forecasting
- Policy impact modeling
- Advanced stakeholder segmentation
- Automated recommendations
- Executive summary narratives
- Advanced statistical models

## Files Created

### Backend Services (5 files)
- `srm_core/srm_core/services/outcome_measurement.py`
- `srm_core/srm_core/services/outcome_progress_tracker.py`
- `srm_core/srm_core/services/dashboard_api.py`
- `srm_core/patches/v1_2/__init__.py`
- `srm_core/patches/v1_2/noop_phase_2.py`

### Tests (2 files)
- `srm_core/srm_core/tests/test_outcome_measurement.py`
- `srm_core/srm_core/tests/test_outcome_progress_tracker.py`

### Configuration
- `srm_core/patches.txt` (updated)

## Next Steps (Phase 3)

1. **AI-Assisted Analysis** — OpenAI integration for insight generation
2. **Attribution Modeling** — Isolate intervention contribution
3. **Contribution Analysis** — Track outcome across multiple interventions
4. **Evidence Confidence Scoring** — Assess measurement quality
5. **Advanced Dashboards** — Executive reporting, drill-down analytics
6. **Predictive Models** — Forecast outcomes based on trend

## Support

**Backend Documentation:**
- `docs/PHASE_2_IMPLEMENTATION_GUIDE.md` (this file)
- `srm_core/srm_core/services/outcome_measurement.py` (measurement logic)
- `srm_core/srm_core/services/outcome_progress_tracker.py` (progress tracking)
- `srm_core/srm_core/services/dashboard_api.py` (API endpoints)

**Testing:**
```bash
pytest srm_core/srm_core/tests/test_outcome_*.py -v
```

**API Testing:**
```bash
curl http://localhost:8000/api/method/srm_core.services.dashboard_api.get_all_interventions_summary
```

---

**Phase 2 is backend-complete and ready for frontend integration by Cursor.**

*Prepared by: GitHub Copilot | Date: September 2, 2026 | Branch: feature/phase-2-outcome-measurement*
