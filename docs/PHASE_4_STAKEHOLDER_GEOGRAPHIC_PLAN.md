# Phase 4: Stakeholder & Geographic Analysis - Architecture & Planning

## Overview

Phase 4 adds analytical dimensions to TrustLedger's measurement architecture by enabling disaggregated outcome analysis.

**Core Question:** Who is experiencing the change, and where is it occurring?

**Problem It Solves:**

Overall results can be misleading:
```
Overall Stakeholder Understanding: 72%

Appears positive, but hides:
  Community Leaders:     91% ✓ Strong
  General Residents:     68% ~ Moderate
  Youth:                 54% ✗ Weak
  
Geographic Breakdown:
  Ward 1:                82% ✓ Strong
  Ward 2:                72% ~ Moderate  
  Ward 3:                64% ~ Moderate
  Ward 4:                43% ✗ Weak
```

Phase 4 makes these differences visible and actionable.

---

## Phase 4 Scope (Simple, Reuse-Focused)

### The Core Principle

**Every measurement should answer:**
- "For whom?" (Stakeholder segment)
- "Where?" (Geographic area)

### Key Boundary

⚠️ **NOT building sophisticated demographic analytics.**

✅ **Simply linking measurements to existing TrustLedger entities:**
- Stakeholder (existing or new)
- Stakeholder Group (existing or new)
- Geographic Area (existing)
- Measurement Record (existing)
- Impact Indicator (existing)
- Impact Snapshot (existing)

**No duplicates. Reuse first.**

---

## Phase 4 Data Architecture

### Extended Measurement Chain

```
Communication Intervention
          ↓
Communication Objective
          ↓
Impact Indicator
          ↓
Measurement Record  ← NEW: Add stakeholder + geographic links
          ↓
Evidence Record
          ↓
Stakeholder Segment  ← NEW
          ↓
Geographic Area
          ↓
Outcome Analysis     ← NEW: Disaggregated view
```

### New Fields (Measurement Record)

Add to existing `Measurement Record` DocType:

```python
{
    "fieldname": "stakeholder_segment",
    "fieldtype": "Link",
    "options": "Stakeholder",  # or "Stakeholder Group" if preferred
    "label": "Stakeholder Segment",
    "description": "Which stakeholder group this measurement represents (optional)",
    "insert_after": "measured_value"
},
{
    "fieldname": "geographic_area",
    "fieldtype": "Link",
    "options": "Geographic Area",
    "label": "Geographic Area",
    "description": "Location where this measurement was collected (optional)",
    "insert_after": "stakeholder_segment"
}
```

**Key Point:** Both fields are **optional**. A measurement can be:
- Overall (no stakeholder or area)
- Stakeholder-only (disaggregated by group, not location)
- Geographic-only (disaggregated by location, not group)
- Both (full disaggregation)

### DocTypes to Check/Create

**Before creating, verify existence:**

1. **Stakeholder** or **Stakeholder Group**
   - If exists: Link to it
   - If not: Create minimal version (name, description)

2. **Geographic Area**
   - Likely exists from Phase 1
   - Verify relationship structure (hierarchy: Country → Region → Ward, etc.)
   - Reuse as-is

3. **Outcome Analysis** (NEW)
   - Lightweight view/calculation layer
   - NOT a stored DocType; generated on-demand
   - Aggregates measurements by stakeholder/area

---

## Phase 4 Display Layer

### Outcome Summary View (Enhanced)

```
╔════════════════════════════════════════════════════════════════════╗
║ UNDERSTANDING OF RELOCATION PROCESS                               ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ OVERALL RESULT                                                   ║
║ ├─ Value: 68%                                                    ║
║ ├─ Target: 75%                                                   ║
║ ├─ Progress: 83.72%                                              ║
║ └─ Status: ✓ ON TRACK                                            ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║ BY STAKEHOLDER GROUP                                              ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ Community Leaders         84% ████████████████░░░░  ✓ ABOVE TARGET║
║ General Residents         68% █████████████░░░░░░░  ~ MODERATE   ║
║ Youth                     51% ██████░░░░░░░░░░░░░░  ✗ BELOW TARGET║
║                                                                    ║
║ [Show all segments] [Filter] [Compare]                           ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║ BY GEOGRAPHIC AREA                                                ║
╠════════════════════════════════════════════════════════════════════╣
║                                                                    ║
║ Ward 1 (Waterfront)       79% ██████████████████░░  ✓ ABOVE TARGET║
║ Ward 2 (Central)          72% █████████████░░░░░░░  ~ MODERATE   ║
║ Ward 3 (South)            64% ████████████░░░░░░░░  ~ MODERATE   ║
║ Ward 4 (Outer)            43% ████████░░░░░░░░░░░░  ✗ BELOW TARGET║
║                                                                    ║
║ [Show all areas] [Filter] [Map View]                             ║
║                                                                    ║
╠════════════════════════════════════════════════════════════════════╣
║ KEY INSIGHTS                                                      ║
║                                                                    ║
║ ⚠️  Ward 4 significantly underperforming (43% vs 68% overall)    ║
║ ⚠️  Youth segment lagging (51% vs 68% overall)                  ║
║ ✓  Community leaders engaged (84% understanding)                ║
║                                                                    ║
║ RECOMMENDATION: Focus additional awareness activities in Ward 4   ║
║                 and among youth demographic.                     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
```

### Disaggregated Measurement Table

```
DISAGGREGATED MEASUREMENTS

Stakeholder Group    Geographic Area    Value    Target    Progress    Status
─────────────────────────────────────────────────────────────────────────────
Community Leaders    Overall            84%      75%       112%        ✓
Residents            Overall            68%      75%       83.72%      ✓
Youth                Overall            51%      75%       54%         ✗
(blank)              Ward 1             79%      75%       101%        ✓
(blank)              Ward 2             72%      75%       93%         ✓
(blank)              Ward 3             64%      75%       81%         ✓
(blank)              Ward 4             43%      75%       54%         ✗
```

### Filter & Compare Interface

```
FILTER:
┌─────────────────────────────────────┐
│ Show results for:                   │
│ ☑ Community Leaders                 │
│ ☑ Residents                         │
│ ☑ Youth                             │
│ ☐ (other groups)                    │
└─────────────────────────────────────┘

COMPARE:
┌─────────────────────────────────────┐
│ Compare groups:                     │
│ [Community Leaders] vs [Youth]       │
│                                      │
│ Delta: +33 percentage points         │
│ (Community Leaders ahead)            │
└─────────────────────────────────────┘
```

---

## Phase 4 Backend Services

### Service: `disaggregation_analysis.py`

**Responsibility:** Calculate disaggregated measurements and comparisons

**Key Functions:**

```python
def get_measurements_by_stakeholder(
    indicator_name: str,
    limit: int = 100
) -> list:
    """
    Get all measurements for an indicator, grouped by stakeholder segment.
    
    Returns:
    [
        {
            "stakeholder_segment": "Community Leaders",
            "measurements": [
                {"date": "2026-07-01", "value": 82},
                {"date": "2026-08-01", "value": 84},
            ],
            "current": 84,
            "average": 83,
            "count": 2
        },
        ...
    ]
    """
    pass

def get_measurements_by_geographic_area(
    indicator_name: str,
    limit: int = 100
) -> list:
    """
    Get all measurements for an indicator, grouped by geographic area.
    
    Returns: Similar structure to stakeholder breakdown
    """
    pass

def get_disaggregated_outcome(
    objective_name: str
) -> dict:
    """
    Get complete disaggregated analysis for an objective.
    
    Returns:
    {
        "objective_name": "...",
        "overall": {
            "value": 68,
            "target": 75,
            "progress": 83.72,
            "status": "On Track"
        },
        "by_stakeholder": [
            {"segment": "Community Leaders", "value": 84, ...},
            ...
        ],
        "by_geographic_area": [
            {"area": "Ward 1", "value": 79, ...},
            ...
        ],
        "insights": [
            {"type": "warning", "message": "Ward 4 significantly underperforming"},
            ...
        ]
    }
    """
    pass

def compare_segments(
    segment_1: str,
    segment_2: str,
    indicator_name: str
) -> dict:
    """
    Compare results between two segments (stakeholder or geographic).
    
    Returns:
    {
        "segment_1": {"name": "...", "value": 84},
        "segment_2": {"name": "...", "value": 51},
        "delta": 33,
        "percent_difference": "64.7%",
        "interpretation": "Segment 1 significantly ahead"
    }
    """
    pass

def identify_underperforming_segments(
    objective_name: str,
    threshold_percent: float = 10  # 10% below overall
) -> list:
    """
    Identify segments performing significantly below overall result.
    
    Returns:
    [
        {
            "segment_type": "stakeholder",  # or "geographic"
            "segment_name": "Youth",
            "value": 51,
            "overall": 68,
            "gap": 17,
            "recommendation": "Consider targeted interventions for youth"
        },
        ...
    ]
    """
    pass

def calculate_consistency_score(
    objective_name: str
) -> dict:
    """
    Calculate how consistent results are across segments (0-100).
    High score = results are similar across all segments (consistent)
    Low score = results vary widely (concentrated in some segments)
    
    Returns:
    {
        "consistency_score": 65,  # 0-100
        "interpretation": "Results moderately consistent",
        "variation": {
            "min": 43,
            "max": 84,
            "range": 41,
            "std_dev": 15.2
        }
    }
    """
    pass
```

### Service: `disaggregation_api.py`

**Responsibility:** REST API endpoints for disaggregated analysis

**Endpoints:**

```
GET /api/method/srm_core.services.disaggregation_api.get_measurements_by_stakeholder
    ?indicator_name=[name]
    → Stakeholder-disaggregated measurements

GET /api/method/srm_core.services.disaggregation_api.get_measurements_by_geographic_area
    ?indicator_name=[name]
    → Geographic-disaggregated measurements

GET /api/method/srm_core.services.disaggregation_api.get_disaggregated_outcome
    ?objective_name=[name]
    → Complete disaggregated analysis + insights

GET /api/method/srm_core.services.disaggregation_api.compare_segments
    ?segment_1=[name]&segment_2=[name]&indicator_name=[name]
    → Comparison between two segments

GET /api/method/srm_core.services.disaggregation_api.identify_underperforming_segments
    ?objective_name=[name]&threshold=[10]
    → Segments below threshold

GET /api/method/srm_core.services.disaggregation_api.calculate_consistency_score
    ?objective_name=[name]
    → Consistency/concentration analysis
```

---

## Phase 4 Frontend Components

### 1. **Outcome Disaggregation Card**
**File:** `src/components/Phase4/OutcomeDisaggregationCard.tsx`

**Shows:**
- Overall result (value, target, progress, status)
- By Stakeholder breakdown (table with progress bars)
- By Geographic Area breakdown (table with progress bars)
- Filter/compare buttons

### 2. **Disaggregated Table Component**
**File:** `src/components/Phase4/DisaggregatedTable.tsx`

**Props:**
- Data (measurements by segment)
- Type ("stakeholder" | "geographic")
- Sortable/filterable

### 3. **Segment Comparison Modal**
**File:** `src/components/Phase4/ComparisonModal.tsx`

**Shows:**
- Side-by-side segment comparison
- Delta (difference)
- Percent difference
- Interpretation

### 4. **Underperformance Alert**
**File:** `src/components/Phase4/UnderperformanceAlert.tsx`

**Shows:**
- Segments below target or overall
- Severity (warning/critical)
- Recommendation

### 5. **Consistency Score Card**
**File:** `src/components/Phase4/ConsistencyScoreCard.tsx`

**Shows:**
- Consistency score (0-100)
- Interpretation (consistent/moderate/concentrated)
- Variation metrics (min, max, range, std dev)

### 6. **Geographic Map View** (Optional Phase 4.5)
**File:** `src/components/Phase4/GeographicOutcomeMap.tsx`

**Shows:**
- Map of geographic areas
- Color-coded by outcome (green/yellow/red)
- Hover for details
- Click to drill down

---

## Phase 4 Workflow

### Step 1: Add Measurement Fields
```
Record Measurement (Existing form, enhanced)
├─ Indicator: [pre-filled]
├─ Date: [date picker]
├─ Value: [number]
├─ Measurement Method: [select]  (Phase 3)
├─ Evidence: [link]               (Phase 3)
├─ Stakeholder Segment: [link]    (NEW - Phase 4)  ← Optional
└─ Geographic Area: [link]        (NEW - Phase 4)  ← Optional
```

### Step 2: View Disaggregated Outcome
```
Open Objective
├─ Overall result: 68%
├─ By Stakeholder Group (if measurements exist)
│  ├─ Community Leaders: 84%
│  ├─ Residents: 68%
│  └─ Youth: 51%
└─ By Geographic Area (if measurements exist)
   ├─ Ward 1: 79%
   ├─ Ward 2: 72%
   ├─ Ward 3: 64%
   └─ Ward 4: 43%
```

### Step 3: Analyze Disaggregation
```
Click "Compare" or "Insights"
├─ Consistency score: 65%  (moderately consistent)
├─ Underperforming segments:
│  ├─ Ward 4: 43% (25% below overall)
│  └─ Youth: 51% (25% below overall)
└─ Recommendation: Focus on Ward 4 and youth outreach
```

---

## Phase 4 Acceptance Criteria

| # | Criterion | Owner |
|---|-----------|-------|
| 1 | Measurement Record has stakeholder_segment field | Backend |
| 2 | Measurement Record has geographic_area field | Backend |
| 3 | Stakeholder/Stakeholder Group DocType exists (or verified) | Backend |
| 4 | Geographic Area DocType linked correctly | Backend |
| 5 | disaggregation_analysis.py service complete | Backend |
| 6 | disaggregation_api.py endpoints functional | Backend |
| 7 | Measurements can be disaggregated by stakeholder | Backend |
| 8 | Measurements can be disaggregated by geographic area | Backend |
| 9 | Comparison function works correctly | Backend |
| 10 | Consistency score calculates accurately | Backend |
| 11 | Underperformance detection identifies correctly | Backend |
| 12 | Disaggregation card component renders | Frontend |
| 13 | Disaggregated table displays data correctly | Frontend |
| 14 | Filters work (by segment/area) | Frontend |
| 15 | Comparison modal works | Frontend |
| 16 | Underperformance alerts display | Frontend |
| 17 | Consistency score card displays | Frontend |
| 18 | Overall + disaggregated views integrated | Frontend |
| 19 | All tests passing | Both |
| 20 | Mobile responsive | Frontend |
| 21 | No breaking changes to Phases 1-3 | Both |
| 22 | End-to-end workflow complete (record → disaggregate → analyze) | Both |

---

## Phase 4 Example Scenario

**Scenario: Ward 12 Housing Awareness Campaign Review**

**Overall Result:**
```
Communication Objective: Increase residents' understanding of relocation
Outcome Type: Understanding
Baseline: 32%
Current: 68%
Target: 75%
Progress: 83.72%
Status: On Track
```

**WITH Phase 4 (Disaggregated):**

```
OVERALL: 68%

BY STAKEHOLDER GROUP:
  Community Leaders: 84% (✓ Above target)
  General Residents:  68% (~ Approaching target)
  Youth:              51% (✗ Below target)
  
BY GEOGRAPHIC AREA:
  Ward 1: 79% (✓ Above target)
  Ward 2: 72% (~ Approaching target)
  Ward 3: 64% (~ Approaching target)
  Ward 4: 43% (✗ Significantly below target)

CONSISTENCY SCORE: 65/100 (Moderately consistent)
Interpretation: Results vary by 41 percentage points
               (43% to 84%), indicating outcome is
               concentrated in some groups/areas.

UNDERPERFORMING SEGMENTS:
  ⚠️  Ward 4: 43% (34% below overall, 55% below target)
  ⚠️  Youth: 51% (25% below overall, 32% below target)

ACTION ITEMS:
  1. Investigate why Ward 4 lags (access? messaging? engagement?)
  2. Develop youth-specific communication strategy
  3. Leverage success in Ward 1 to inform Ward 4 approach
  4. Increase community leader involvement in youth outreach
```

**Practitioner Insight:**
- "Program is on track overall, but Ward 4 and youth need urgent attention."
- "Community leaders understand; now need to engage general residents and youth."
- "Geographic disparity larger than demographic disparity."

---

## Phase 4 Integration with Phases 1-3

```
PHASE 1: Define What
  Intervention → Objective → Indicator → Measurement
  
PHASE 2: Measure If
  Baseline → Current → Target → Progress → Status → Trend
  
PHASE 3: Prove How
  Measurement → Evidence → Source → Verification → Attachment
  
PHASE 4: Analyze Who & Where
  Measurement + Stakeholder Segment → Disaggregated Outcome
  Measurement + Geographic Area → Disaggregated Outcome
  → Comparison → Consistency → Insights
```

**Phase 4 doesn't replace Phases 1-3.** It adds analytical dimensions.

All previous functionality remains intact and enhanced by disaggregation.

---

## What Phase 4 Does NOT Include

❌ **Out of Scope:**
- Causal attribution (Phase 5+)
- Contribution analysis (Phase 5+)
- Demographic modeling (Phase 5+)
- Predictive segmentation (Phase 5+)
- AI-driven recommendations (Phase 5+)
- Advanced statistical models (Phase 5+)

✅ **Phase 4 Focus:** Simple, reusable linking of existing entities.

---

## Phase 4 Implementation Timeline

**Backend (Copilot):** 2-3 days
- Add measurement fields
- Create disaggregation services
- Create API endpoints
- Write tests

**Frontend (Cursor):** 2-3 days
- Build disaggregation components
- Implement filters/compare
- Integrate into outcome views
- Write tests

**Total:** 4-6 days (parallel frontend/backend after core is ready)

---

## Phase 4 Progression

```
PHASE 1: WHAT ARE WE TRYING TO CHANGE?
├─ Intervention
├─ Objective
├─ Indicator
├─ Measurement
└─ Snapshot
       ↓

PHASE 2: IS THE CHANGE OCCURRING?
├─ Current Value
├─ Target Value
├─ Progress %
├─ Status
└─ Trend
       ↓

PHASE 3: WHAT EVIDENCE SUPPORTS THE CHANGE?
├─ Measurement Method
├─ Evidence Record
├─ Evidence Type
├─ Collection Date
├─ Source
├─ Verification Status
└─ Attachments
       ↓

PHASE 4: WHO AND WHERE IS THE CHANGE OCCURRING?
├─ Stakeholder Segment
├─ Geographic Area
├─ Disaggregated Measurement
├─ Segment Comparison
├─ Consistency Score
└─ Underperformance Detection
```

---

## Files to Create (Phase 4 Backend)

```
srm_core/
├── srm_core/
│   ├── services/
│   │   ├── disaggregation_analysis.py  ← NEW service
│   │   └── disaggregation_api.py  ← NEW API endpoints
│   └── tests/
│       ├── test_disaggregation_analysis.py  ← NEW tests
│       └── test_disaggregation_api.py  ← NEW tests
├── patches/
│   └── v1_4/
│       ├── __init__.py
│       └── add_disaggregation_fields.py  ← Add fields to Measurement Record
└── patches.txt  ← Updated registry
```

---

## Next: Phase 5+

**Phase 5 capabilities (future):**
- Contribution analysis (multiple interventions → shared outcome)
- Attribution modeling (isolating intervention effect)
- Demographic segmentation (ML-assisted grouping)
- Confidence scoring (measurement quality assessment)
- Predictive analytics (forecast by segment)
- Policy impact modeling
- AI-driven recommendations

**For now: Phase 4 establishes who benefits and where.**

---

## Support & Resources

**TrustLedger Architecture:**
- Phase 1 Guide: `docs/PHASE_1_IMPLEMENTATION_GUIDE.md`
- Phase 2 Guide: `docs/PHASE_2_IMPLEMENTATION_GUIDE.md`
- Phase 3 Guide: `docs/PHASE_3_EVIDENCE_LAYER_PLAN.md`
- Phase 4 Guide: This document

---

**Phase 4 transforms TrustLedger from "What changed?" to "Who benefited and where?"**

*Prepared by: GitHub Copilot | Date: September 2, 2026 | Branch: feature/phase-4-stakeholder-geographic*
