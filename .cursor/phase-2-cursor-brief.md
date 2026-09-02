# Phase 2: Outcome Measurement & Dashboard - Cursor Brief

## Handoff Overview

This document provides Cursor with everything needed to build the Phase 2 frontend and complete end-to-end testing.

**Status:** Backend implementation complete and tested. Ready for:
1. Frontend component integration
2. Dashboard and trend visualization
3. Measurement recording workflow
4. End-to-end testing

---

## Context

### What Backend Built (Phase 2)

Three production-ready services with no new DocTypes:

**1. Outcome Measurement Service** (`outcome_measurement.py`)
- Record measurements by outcome type (6 types: Awareness, Understanding, Trust, Participation, Behaviour Change, Service Uptake)
- Retrieve measurements linked to objectives
- Validate outcome types

**2. Outcome Progress Tracker** (`outcome_progress_tracker.py`)
- Calculate progress % from baseline → current → target
- Infer status: On Track / Needs Attention / Off Track / No Data
- Track historical trend
- Aggregate multiple objectives

**3. Dashboard API** (`dashboard_api.py`)
- 4 REST endpoints for frontend
- Fully documented with query params
- Permission-checked (whitelist decorators)

### Key Endpoints

```
GET /api/method/srm_core.services.dashboard_api.get_intervention_dashboard
    ?intervention_name=[name]
    → Returns: overall_progress_pct, outcomes by type

GET /api/method/srm_core.services.dashboard_api.get_objective_progress
    ?objective_name=[name]
    → Returns: baseline, current, target, progress_pct, status

GET /api/method/srm_core.services.dashboard_api.get_outcome_trend_api
    ?objective_name=[name]
    → Returns: baseline, measurements[], target

GET /api/method/srm_core.services.dashboard_api.get_all_interventions_summary
    → Returns: all interventions with aggregated progress
```

---

## Frontend Integration Tasks

### 1. **API Service Module** (Priority: 1)

**File:** `src/services/outcomeService.ts`

**Functions needed:**

```typescript
// Get intervention dashboard
getInterventionDashboard(interventionName: string): Promise<InterventionDashboard>

// Get single objective progress
getObjectiveProgress(objectiveName: string): Promise<OutcomeProgress>

// Get trend data for objective
getOutcomeTrend(objectiveName: string): Promise<OutcomeTrend>

// Get all interventions summary
getAllInterventionsSummary(): Promise<DashboardSummary>

// Record measurement (existing, reuse from Phase 1)
createMeasurement(data: MeasurementRecord): Promise<any>
```

**Base URL:** Use existing API base from env config

**Error Handling:** 
- 401/403 → Redirect to login
- 404 → Show "Not found" message
- 500 → Show "Server error" toast
- Network error → Show "Connection failed" toast

**Implementation note:** Keep this service separate from Phase 1's `communicationImpactService.ts` for now. We can merge later if needed.

---

### 2. **Type Definitions** (Priority: 1)

**File:** `src/types/outcomePhase2.ts`

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
  status_color: string;  // #hex
  last_measurement_date: string | null;  // YYYY-MM-DD
  measurements_count: number;
}

export interface MeasurementTrendPoint {
  date: string;  // YYYY-MM-DD
  value: number;
}

export interface OutcomeTrend {
  baseline: number;
  measurements: MeasurementTrendPoint[];
  target: number;
}

export interface InterventionDashboard {
  intervention_name: string;
  overall_progress_pct: number | null;
  outcomes: Record<OutcomeType, OutcomeProgress>;
  total_objectives: number;
  objectives_on_track: number;
  last_updated: string;  // ISO datetime
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

---

### 3. **Outcome Progress Card Component** (Priority: 2)

**File:** `src/components/Phase2/OutcomeProgressCard.tsx`

**Props:**
```typescript
interface OutcomeProgressCardProps {
  objective: OutcomeProgress;
  onViewTrend?: () => void;
  onRecordMeasurement?: () => void;
}
```

**Displays:**
```
┌─────────────────────────────────────┐
│ UNDERSTANDING                    │  │ ← outcome type badge
├─────────────────────────────────────┤
│ 32% → 68% → 75%                     │ ← baseline → current → target
│ ████████░░░░░░ 83.72%              │ ← progress bar + %
│ Status: ✅ ON TRACK                │ ← colored badge
├─────────────────────────────────────┤
│ Last measured: Jul 20, 2026         │ ← date
│ Measurements: 3                     │ ← count
│ [View Trend] [Record Measurement]   │ ← buttons
└─────────────────────────────────────┘
```

**Colors:**
- On Track → Green (#10B981)
- Needs Attention → Amber (#F59E0B)
- Off Track → Red (#EF4444)
- No Data → Gray (#9CA3AF)

**Progress Bar:**
- Background: Light gray
- Fill: Color based on status
- Label: Progress percentage
- Markers: Baseline point (left), target point (right)

**Interactions:**
- Click "View Trend" → Open trend modal/page
- Click "Record Measurement" → Open measurement form
- Hover numbers → Tooltip showing calculation

---

### 4. **Trend Visualization Component** (Priority: 2)

**File:** `src/components/Phase2/TrendChart.tsx`

**Props:**
```typescript
interface TrendChartProps {
  trend: OutcomeTrend;
  objectiveName: string;
  outcomeType: OutcomeType;
  onClose?: () => void;
}
```

**Display Options (pick one to start, can expand):**

Option A: Simple Line Chart (Recommended)
```
100% ┤
     │                              ╱─ Target
 75% ├────────────────────────────╱─────────
     │                    ╱╱╱╱╱╱╱
 50% ┤              ╱╱╱╱╱
     │        ╱╱╱╱╱
 25% ├  ╱╱╱╱╱  ← Baseline
     │
  0% └─────────────────────────────────────
     Base M1  M2  M3  M4  ...     Target
```

Option B: Vertical Bar Chart
```
100% ┤
 75% ├  ║
     │  ║     ║
 50% ┤  ║     ║     ║
     │  ║     ║     ║
 25% ├  ║     ║     ║     ║
     │
  0% └──32──41──56──68───Tgt
```

Option C: Sparkline + Table
```
Trend: ↗ (ascending)
╭─────┬──────┬──────────┐
│Date │Value │Change    │
├─────┼──────┼──────────┤
│Base │ 32%  │    -     │
│M1   │ 41%  │ +9% (↑)  │
│M2   │ 56%  │ +15% (↑) │
│M3   │ 68%  │ +12% (↑) │
│Tgt  │ 75%  │ +7% ▶    │
╰─────┴──────┴──────────╯
```

**Requirements:**
- X-axis: Measurement points (Baseline, M1, M2, ... Target)
- Y-axis: Values (0-100% or custom range)
- Baseline point: Different color/style (e.g., dashed line)
- Target point: Horizontal line at target value
- Current point: Highlighted/bold
- Hover: Show value, date, change from previous
- Responsive: Stack vertically on mobile

**Library options:**
- Recharts (recommended, light)
- Chart.js
- D3.js (overkill but powerful)
- Plotly.js
- Simple canvas/SVG if minimal dependencies

---

### 5. **Intervention Detail View** (Priority: 2)

**File:** `src/components/Phase2/InterventionDetailView.tsx` or page route

**Props/Route:**
```typescript
// If component:
interface InterventionDetailViewProps {
  interventionName: string;
  onClose?: () => void;
}

// If page route:
// /communication-impact/intervention/[name]
```

**Layout:**

```
┌─────────────────────────────────────┐
│ Ward 12 Housing Awareness Campaign  │
│ Status: Active | Start: Aug 1, 2026 │
├─────────────────────────────────────┤
│                                     │
│ OVERALL PROGRESS: 61%               │
│ ████████░░░░░░░░░░░░ 6 objectives  │
│ 2 On Track | 4 Needs Attention      │
│                                     │
├─────────────────────────────────────┤
│ OBJECTIVES BY OUTCOME TYPE:         │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ AWARENESS                       │ │
│ │ 32% → 78% → 85%                 │ │
│ │ ████████░░░ 78% ✅ ON TRACK    │ │
│ │ [View Trend] [Record]           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ UNDERSTANDING                   │ │
│ │ 32% → 68% → 75%                 │ │
│ │ ██████████░░░░ 83.72% ✅ TRACK │ │
│ │ [View Trend] [Record]           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ TRUST                           │ │
│ │ 40% → 50% → 70%                 │ │
│ │ ███████░░░░░░░░░░░░░░ 62% ⚠️   │ │
│ │ [View Trend] [Record]           │ │
│ └─────────────────────────────────┘ │
│                                     │
│ (More outcome type cards below...)  │
│                                     │
└─────────────────────────────────────┘
```

**Data Flow:**
1. Component mounts
2. Fetch intervention dashboard: `getInterventionDashboard(name)`
3. Display overall progress card
4. Loop through outcomes object, create OutcomeProgressCard for each
5. Each card loads independently

**Interactions:**
- Click "View Trend" on any card → Open TrendChart modal/page for that objective
- Click "Record Measurement" → Open measurement form for that objective
- Refresh button (top right) → Reload data from API

**Loading state:**
- Show skeleton cards while fetching
- "Loading..." spinner

**Error handling:**
- If intervention not found → Show "Intervention not found"
- If network error → Show error toast with retry

---

### 6. **Outcome Dashboard** (Priority: 3)

**File:** `src/components/Phase2/OutcomeDashboard.tsx` or page route

**Route:** `/communication-impact/dashboard`

**Layout:**

```
┌──────────────────────────────────────────┐
│ COMMUNICATION IMPACT DASHBOARD           │
├──────────────────────────────────────────┤
│                                          │
│ SUMMARY CARDS:                           │
│ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐   │
│ │Total │ │ Avg  │ │  On  │ │Needs │   │
│ │Inter-│ │Prog. │ │Track │ │Atten.│   │
│ │ vens │ │  %   │ │      │ │      │   │
│ │  6   │ │  61% │ │  2   │ │  4   │   │
│ └──────┘ └──────┘ └──────┘ └──────┘   │
│                                          │
├──────────────────────────────────────────┤
│                                          │
│ INTERVENTIONS:                           │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Ward 12 Housing Awareness Campaign │  │
│ │ Status: Active | Progress: 61%     │  │
│ │                                    │  │
│ │ Awareness         ████░░░░░░ 78%  │  │
│ │ Understanding     ██████░░░░ 83%  │  │
│ │ Trust             ██████░░░░ 62%  │  │
│ │ Participation     █████░░░░░ 55%  │  │
│ │ Behaviour         ████░░░░░░ 48%  │  │
│ │ Service Uptake    ████░░░░░░ 43%  │  │
│ │                                    │  │
│ │ [View Details] [Edit]              │  │
│ └────────────────────────────────────┘  │
│                                          │
│ ┌────────────────────────────────────┐  │
│ │ Community Health Initiative         │  │
│ │ Status: Draft | Progress: 52%      │  │
│ │                                    │  │
│ │ Awareness         ███░░░░░░░ 52%  │  │
│ │ Understanding     █████░░░░░ 71%  │  │
│ │                                    │  │
│ │ [View Details] [Edit]              │  │
│ └────────────────────────────────────┘  │
│                                          │
│ (More intervention cards below...)       │
│                                          │
└──────────────────────────────────────────┘
```

**Data Flow:**
1. Page mounts
2. Fetch all interventions: `getAllInterventionsSummary()`
3. Display summary cards (total, avg progress, on-track count)
4. Loop through interventions, create card for each
5. For each intervention, show only outcome types with data

**Features:**
- Summary cards show key metrics
- Intervention cards show only populated outcome types
- Progress bars for each outcome type
- Click card to navigate to intervention detail
- Responsive: Stack on mobile
- Loading skeleton while fetching

**Sorting/Filtering (Phase 2 optional, can add Phase 2.5):**
- Sort by: Name, Progress %, Status
- Filter by: Status (Draft/Active/Completed), Outcome Type

---

### 7. **Measurement Recording Form** (Priority: 2)

**File:** `src/components/Phase2/RecordMeasurementModal.tsx`

**Context:** This already exists from Phase 1, but Phase 2 needs to integrate it into the Trend View and Intervention Detail.

**Phase 2 Enhancement:**
- Pre-fill objective_name
- Auto-set measurement date to today
- Post-save: Refresh trend chart / intervention detail
- Show success toast: "Measurement recorded. Updating snapshot..."
- Show loading while snapshot generates

**Form fields:**
```
Objective: [Pre-filled, read-only]
Date: [Date picker, default today]
Value: [Number input]
Notes: [Text area, optional]
[Cancel] [Save]
```

**On submit:**
```typescript
POST /api/resource/Measurement Record
{
  "impact_indicator": objective.impact_indicator,
  "measurement_date": form.date,
  "measured_value": form.value,
  "notes": form.notes
}
```

**On success:**
- Toast: "Measurement saved successfully"
- Wait 1-2 seconds (for snapshot generation)
- Refresh parent component data
- Close modal

---

## Implementation Prompts for Cursor

### Prompt 1: API Service Module

```
You are building the outcome measurement service for Phase 2 frontend.

File: src/services/outcomeService.ts

Create a TypeScript service with these methods:

1. getInterventionDashboard(interventionName: string): Promise<InterventionDashboard>
   - Endpoint: /api/method/srm_core.services.dashboard_api.get_intervention_dashboard
   - Query: ?intervention_name=[name]
   - Returns: dashboard data with all objectives aggregated

2. getObjectiveProgress(objectiveName: string): Promise<OutcomeProgress>
   - Endpoint: /api/method/srm_core.services.dashboard_api.get_objective_progress
   - Query: ?objective_name=[name]
   - Returns: progress data with status

3. getOutcomeTrend(objectiveName: string): Promise<OutcomeTrend>
   - Endpoint: /api/method/srm_core.services.dashboard_api.get_outcome_trend_api
   - Query: ?objective_name=[name]
   - Returns: trend data (baseline, measurements[], target)

4. getAllInterventionsSummary(): Promise<DashboardSummary>
   - Endpoint: /api/method/srm_core.services.dashboard_api.get_all_interventions_summary
   - No query params
   - Returns: all interventions with aggregated data

Error handling:
- Catch 401/403 → throw AuthError
- Catch 404 → throw NotFoundError
- Catch 500+ → throw ServerError
- Network errors → throw NetworkError

Base URL: Use process.env.NEXT_PUBLIC_API_URL or fallback to http://localhost:8000

Headers: Include Authorization header if token available

Return: Fully working service module with proper types.
```

### Prompt 2: Type Definitions

```
Create comprehensive TypeScript types for Phase 2 outcome measurement.

File: src/types/outcomePhase2.ts

Include:
- OutcomeType (union of 6 types)
- OutcomeStatus (4 status values)
- OutcomeProgress (interface with all progress fields)
- MeasurementTrendPoint (date + value)
- OutcomeTrend (baseline, measurements[], target)
- InterventionDashboard (dashboard data structure)
- DashboardSummary (all interventions summary)

All with:
- JSDoc comments explaining fields
- Optional fields marked with ?
- Proper type annotations (no any)
- Enums for controlled values (OutcomeType, OutcomeStatus)

Return: Types file ready to import in components and services.
```

### Prompt 3: Outcome Progress Card

```
Build the OutcomeProgressCard component for Phase 2.

File: src/components/Phase2/OutcomeProgressCard.tsx

Props:
- objective: OutcomeProgress (required)
- onViewTrend?: () => void (optional callback)
- onRecordMeasurement?: () => void (optional callback)

Display:
- Outcome type as a badge/label at top (Awareness, Understanding, etc)
- Three values: Baseline → Current → Target (e.g., "32% → 68% → 75%")
- Progress bar:
  - Background light gray
  - Fill color based on status (green/amber/red/gray)
  - Show percentage number inside bar
  - Baseline marker at left, target marker at right
- Status badge (colored):
  - On Track → Green with checkmark
  - Needs Attention → Amber with warning icon
  - Off Track → Red with X
  - No Data → Gray
- Last measurement date
- Number of measurements recorded
- Two buttons:
  - "View Trend" → calls onViewTrend callback
  - "Record Measurement" → calls onRecordMeasurement callback

Styling:
- Card layout with subtle shadow/border
- Responsive: full width on mobile, grid on desktop
- Colors from design system (or use hex provided)
- Professional, clean design

Interactivity:
- Hover on numbers → show calculation tooltip
- Click buttons → trigger callbacks
- Loading state if needed

Return: Reusable component ready for InterventionDetailView.
```

### Prompt 4: Trend Chart

```
Build a trend visualization component for Phase 2.

File: src/components/Phase2/TrendChart.tsx

Props:
- trend: OutcomeTrend (required) - has baseline, measurements[], target
- objectiveName: string (required) - for display
- outcomeType: OutcomeType (required) - for label
- onClose?: () => void (optional callback)

Choose visualization style (pick one, implement as-is):

Option A: Line Chart (Recommended)
- Use Recharts library
- X-axis: Points (Baseline, M1, M2, M3, ..., Target)
- Y-axis: Values (0-100% range recommended)
- Line from baseline through measurements to target
- Baseline point: dashed/different style
- Target point: horizontal line
- Current point (last measurement): highlight/bold
- Hover tooltip showing value, date, change
- Responsive grid

Option B: Bar Chart
- Recharts BarChart
- Bars for each measurement point
- Baseline and target as reference lines
- Same hover/tooltip behavior

Option C: Table + Sparkline
- Simple table: Date | Value | Change
- Sparkline chart above (tiny line showing trend)
- Text-based, lightweight

Requirements (all options):
- Must show baseline at start
- Must show target as end goal
- Must show all measurements in order
- Must show current value highlighted
- Hover tooltip with calculation or explanation
- Mobile responsive (stack vertically if needed)
- Load animation if needed
- Error state if no data

Return: Working trend visualization component.
```

### Prompt 5: Intervention Detail View

```
Build the intervention detail page/component for Phase 2.

File: src/pages/communication-impact/intervention/[name].tsx
  OR src/components/Phase2/InterventionDetailView.tsx

Functionality:
1. Accept intervention name (from route params or prop)
2. Fetch dashboard data: getInterventionDashboard(name)
3. Display intervention header:
   - Name
   - Status badge
   - Date range (if available)
4. Display overall progress:
   - Percentage
   - Progress bar
   - Breakdown: X On Track, Y Needs Attention, etc
5. Display objectives grouped by outcome type:
   - For each outcome type with data:
     - Create OutcomeProgressCard component
     - Pass objective data, callbacks
6. Callbacks:
   - "View Trend" → Open TrendChart modal/page
   - "Record Measurement" → Open measurement form modal
7. Refresh button (top right) → Reload data
8. Loading state while fetching
9. Error handling with retry
10. Mobile responsive

Data flow:
- Fetch intervention dashboard
- Extract outcomes object
- Map to OutcomeProgressCard components
- Handle modals for trend view and measurement recording

Return: Fully functional intervention detail view.
```

### Prompt 6: Outcome Dashboard

```
Build the main outcome dashboard for Phase 2.

File: src/pages/communication-impact/dashboard.tsx
  OR src/components/Phase2/OutcomeDashboard.tsx

Functionality:
1. Fetch all interventions: getAllInterventionsSummary()
2. Display summary cards (top):
   - Total interventions
   - Average progress %
   - Number on track
   - Number needing attention
3. Display intervention cards (grid/list):
   - For each intervention in response:
     - Intervention name
     - Status badge
     - Overall progress % + bar
     - For each outcome type with data:
       - Outcome type label
       - Progress bar
       - Progress % number
   - Click to navigate to intervention detail
4. Refresh button
5. Loading skeleton while fetching
6. Empty state if no interventions
7. Error handling
8. Mobile responsive (stack vertically)

Styling:
- Summary cards: prominent at top
- Intervention cards: grid (3 cols desktop, 1 col mobile)
- Each card: clear hierarchy, shadow/border
- Status badges: color-coded
- Progress bars: consistent with OutcomeProgressCard

Return: Production-ready dashboard.
```

### Prompt 7: Measurement Recording Integration

```
Integrate measurement recording into Phase 2 components.

You already have a RecordMeasurementForm from Phase 1.

In Phase 2, enhance it:

1. When "Record Measurement" button clicked in OutcomeProgressCard:
   - Open modal with pre-filled objective name
   - Set date to today by default
   - Show form fields: Date, Value, Notes

2. On form submit:
   - POST to /api/resource/Measurement Record
   - Show loading spinner
   - On success:
     - Show toast: "Measurement recorded successfully"
     - Wait 1-2 seconds for snapshot generation
     - Close modal
     - Refresh parent component (re-fetch dashboard)
     - Show updated progress card
   - On error:
     - Show error toast with message
     - Keep modal open

3. Add loading state feedback:
   - "Saving..." text while POSTing
   - "Updating snapshot..." while waiting
   - Spinner animations

4. Mobile: Make modal full-screen or swipe-dismissible

Return: Fully integrated measurement workflow.
```

### Prompt 8: Integration Tests

```
Write integration tests for Phase 2 components.

File: src/__tests__/phase2.integration.test.ts

Using Jest or your test framework:

Test Suite: "Phase 2 Outcome Measurement"

1. Test: Intervention detail page loads and displays objectives
   - Mock API: getInterventionDashboard returns test data
   - Render InterventionDetailView
   - Verify intervention name displays
   - Verify all outcome type cards render
   - Verify progress bars show correct %

2. Test: Outcome progress card displays status correctly
   - Test On Track status (green)
   - Test Needs Attention status (amber)
   - Test Off Track status (red)
   - Test No Data status (gray)
   - Verify buttons are clickable

3. Test: Trend chart renders with data
   - Mock API: getOutcomeTrend returns test data
   - Render TrendChart
   - Verify all measurement points display
   - Verify baseline and target show
   - Verify current point highlighted

4. Test: Dashboard loads all interventions
   - Mock API: getAllInterventionsSummary returns test data
   - Render OutcomeDashboard
   - Verify summary cards show correct numbers
   - Verify intervention cards render
   - Verify each outcome type shows correctly

5. Test: Measurement recording workflow
   - Mock API: createMeasurement succeeds
   - Click "Record Measurement" button
   - Fill form: date, value
   - Submit form
   - Verify success toast appears
   - Verify modal closes
   - Verify data refreshed

6. Test: Error handling
   - Mock API: getInterventionDashboard returns 404
   - Verify "Not found" error displays
   - Verify retry button works
   - Mock API: network error
   - Verify "Connection failed" toast shows

Return: Comprehensive test suite with all tests passing.
```

### Prompt 9: End-to-End Workflow Test

```
Create an end-to-end test simulating the Ward 12 example workflow.

File: src/__tests__/phase2.e2e.ward12.test.ts

Test: "Ward 12 Housing Awareness Campaign - Complete Workflow"

Steps:
1. Navigate to dashboard
2. Verify "Ward 12 Housing Awareness Campaign" intervention displays
3. Verify progress shows 61% overall
4. Verify 6 outcome types visible (Awareness, Understanding, Trust, etc)
5. Verify each shows correct progress % (78%, 83%, 62%, 55%, 48%, 43%)
6. Click "Understanding" card
7. Verify detail shows:
   - Baseline: 32%
   - Current: 68%
   - Target: 75%
   - Progress: 83.72%
   - Status: On Track
8. Click "View Trend"
9. Verify trend chart shows:
   - Baseline: 32%
   - Month 1: 41% (+9%)
   - Month 2: 56% (+15%)
   - Month 3: 68% (+12%)
   - Target: 75%
10. Click "Record Measurement"
11. Record new measurement:
    - Date: Today
    - Value: 71
12. Verify success toast
13. Verify snapshot updates:
    - Current: 71% (was 68%)
    - Progress: 87.21% (was 83.72%)
14. Verify trend chart updates with new point
15. Return to dashboard
16. Verify Understanding progress updated to 87.21%
17. Verify overall intervention progress recalculated

Expected outcome: Full workflow completes without errors, all values update correctly.
```

---

## Testing Checklist

### Unit Tests
- [ ] API service makes correct fetch calls
- [ ] Type definitions compile without errors
- [ ] OutcomeProgressCard renders with all props
- [ ] TrendChart displays measurements correctly
- [ ] Status badges show correct colors
- [ ] Progress bars calculate correctly

### Integration Tests
- [ ] Intervention detail loads and displays
- [ ] Dashboard aggregates interventions correctly
- [ ] Trend modal opens/closes
- [ ] Measurement form submits
- [ ] Success/error toasts appear
- [ ] Data refreshes after recording measurement

### E2E Tests
- [ ] Ward 12 workflow completes
- [ ] Progress calculations accurate
- [ ] Trend shows all measurements in order
- [ ] New measurements update dashboard
- [ ] Mobile responsive on all pages
- [ ] No console errors

### Manual Testing (Browser)
- [ ] Navigate to dashboard → interventions load
- [ ] Click intervention → detail view loads
- [ ] Click "View Trend" → chart displays
- [ ] Click "Record Measurement" → form opens
- [ ] Fill form, submit → measurement saved
- [ ] Trend updates with new point
- [ ] Dashboard progress updates
- [ ] All dates formatted consistently
- [ ] All numbers show 2 decimal places
- [ ] Mobile: tap card → detail loads
- [ ] Mobile: scroll trend chart → works smoothly

---

## Key Formulas

### Progress Calculation
```
Progress % = ((Current - Baseline) / (Target - Baseline)) × 100

Example:
- Baseline: 32%
- Current: 68%
- Target: 75%
- Progress: ((68-32)/(75-32)) × 100 = (36/43) × 100 = 83.72%
```

### Status Inference
```
If Current ≥ Target → "On Track" (actually completed)
Else if Progress ≥ 80% → "On Track"
Else if Progress > 0% → "Needs Attention"
Else if Progress ≤ 0% → "Off Track" (or "No Data" if null)
```

---

## Files to Create

```
src/
├── services/
│   └── outcomeService.ts (API calls)
├── types/
│   └── outcomePhase2.ts (TypeScript interfaces)
├── components/Phase2/
│   ├── OutcomeProgressCard.tsx
│   ├── TrendChart.tsx
│   ├── InterventionDetailView.tsx
│   └── OutcomeDashboard.tsx
├── pages/communication-impact/
│   ├── dashboard.tsx (or use component above)
│   └── intervention/
│       └── [name].tsx (or use component above)
└── __tests__/
    ├── phase2.integration.test.ts
    └── phase2.e2e.ward12.test.ts
```

---

## Dependencies (If Not Already Installed)

```json
{
  "recharts": "^2.x",  // For charts (or your preference)
  "react-hot-toast": "^2.x",  // For notifications
  "date-fns": "^3.x"  // For date formatting
}
```

---

## Deployment

### Local Testing
1. Backend running: `bench start`
2. Frontend dev: `npm run dev`
3. Test endpoints in browser: `http://localhost:3000`

### Production
1. Build: `npm run build`
2. Deploy: Follow your deployment process
3. Backend must be accessible: `process.env.NEXT_PUBLIC_API_URL`

---

## Support & Questions

**Phase 2 Backend Docs:**
- `docs/PHASE_2_IMPLEMENTATION_GUIDE.md` (in srm-core repo)
- `srm_core/services/outcome_measurement.py`
- `srm_core/services/outcome_progress_tracker.py`
- `srm_core/services/dashboard_api.py`

**Test Backend Locally:**
```bash
curl http://localhost:8000/api/method/srm_core.services.dashboard_api.get_all_interventions_summary
```

**If API returns 404:**
- Verify Frappe migration ran: `bench --site [site] migrate`
- Check logs: `bench logs -f`
- Restart bench: `bench restart`

---

## Handoff Checklist

When finished, verify:
- [ ] All components render correctly
- [ ] All API calls work (test in browser)
- [ ] Progress % calculations accurate
- [ ] Status badges show correct colors
- [ ] Trend visualization displays measurements
- [ ] Measurement recording works end-to-end
- [ ] Dashboard aggregates all interventions
- [ ] Mobile responsive (tested on mobile/tablet)
- [ ] All error states handled
- [ ] Loading states visible
- [ ] Success toasts appear
- [ ] Ward 12 workflow completes successfully
- [ ] All tests passing
- [ ] No console errors
- [ ] Code is well-commented
- [ ] Types fully defined

---

**Phase 2 frontend is ready to build. Use the prompts above in sequence.**

*Prepared by: GitHub Copilot | Date: September 2, 2026 | Branch: feature/phase-2-outcome-measurement*
