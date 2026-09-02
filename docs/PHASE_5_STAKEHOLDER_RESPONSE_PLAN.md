# Phase 5: Stakeholder Response & Feedback - Architecture & Planning

## Overview

Phase 5 adds the qualitative dimension to TrustLedger by systematically capturing, classifying, and analyzing stakeholder responses and feedback.

**Core Question:** What are stakeholders saying about the intervention?

**The Problem It Solves:**

Quantitative measurements alone can be misleading:

```
Measured Outcome: Understanding = 68%

But stakeholder feedback reveals:
  "We understand relocation is happening,
   but nobody explained what documents we need."
```

Phase 5 captures this voice and connects it to measurements, revealing discrepancies and themes that numbers alone cannot expose.

---

## Phase 5 Scope: Simple, Structured, Manual

### Core Principle

**NOT building AI sentiment analysis yet.**

Phase 5 establishes clean, structured stakeholder-response data through:
- Manual classification by practitioners
- Simple controlled values
- Clear linking to interventions, objectives, stakeholders, and locations
- Searchable, filterable feedback database

### Key Boundary

❌ **Out of Scope (Phase 6+):**
- AI sentiment analysis
- Automated theme extraction
- NLP processing
- Predictive sentiment modeling
- Automated recommendations
- Early Warning Engine
- Root-cause analysis
- Contribution analysis
- Attribution modeling

✅ **Phase 5 Focus:** Capture stakeholder voice as structured data.

---

## Phase 5 Core Concept: Stakeholder Response

### Definition

**Stakeholder Response:** An individual piece of feedback received from a stakeholder or stakeholder group about a communication/engagement intervention.

### Sources

A Stakeholder Response can originate from:
- Survey
- Interview
- Focus group
- Community meeting
- Public participation process
- Grievance/complaint
- Field engagement
- Email
- Digital platform
- Facilitator observation
- Other approved source

### Guiding Principle

Every response is:
- **Individual** - One piece of feedback
- **Traceable** - Linked to source and date
- **Contextual** - Connected to intervention, objective, stakeholder, location
- **Classified** - Assigned type, theme, sentiment
- **Searchable** - Discoverable via filters
- **Actionable** - Raises awareness of themes and patterns

---

## Stakeholder Response DocType Structure

### Core Fields

```python
{
    "doctype": "Stakeholder Response",
    "fields": [
        {
            "fieldname": "response_text",
            "fieldtype": "Text Editor",
            "label": "Response",
            "description": "The actual feedback or comment from stakeholder",
            "reqd": True
        },
        {
            "fieldname": "response_date",
            "fieldtype": "Date",
            "label": "Response Date",
            "description": "When was this feedback received?",
            "reqd": True
        },
        {
            "fieldname": "stakeholder",
            "fieldtype": "Link",
            "options": "Stakeholder",
            "label": "Stakeholder",
            "description": "Specific stakeholder who provided feedback (optional)",
            "reqd": False
        },
        {
            "fieldname": "stakeholder_group",
            "fieldtype": "Link",
            "options": "Stakeholder Group",
            "label": "Stakeholder Group",
            "description": "Which stakeholder group does this relate to? (optional)",
            "reqd": False
        },
        {
            "fieldname": "geographic_area",
            "fieldtype": "Link",
            "options": "Geographic Area",
            "label": "Geographic Area",
            "description": "Where did this feedback originate? (optional)",
            "reqd": False
        },
        {
            "fieldname": "intervention",
            "fieldtype": "Link",
            "options": "Communication Intervention",
            "label": "Intervention",
            "description": "Related communication/engagement intervention",
            "reqd": False
        },
        {
            "fieldname": "objective",
            "fieldtype": "Link",
            "options": "Communication Objective",
            "label": "Communication Objective",
            "description": "Which objective does this feedback relate to? (optional)",
            "reqd": False
        },
        {
            "fieldname": "response_type",
            "fieldtype": "Select",
            "label": "Response Type",
            "description": "What kind of response is this?",
            "options": [
                "Question",
                "Suggestion",
                "Concern",
                "Complaint",
                "Positive Feedback",
                "Negative Feedback",
                "Request for Information",
                "Request for Assistance",
                "Other"
            ],
            "reqd": True
        },
        {
            "fieldname": "theme",
            "fieldtype": "Select",
            "label": "Theme",
            "description": "Main subject/topic of this response",
            "options": [
                "Programme Understanding",
                "Eligibility",
                "Process",
                "Service Access",
                "Trust",
                "Participation",
                "Timing",
                "Documentation",
                "Compensation",
                "Relocation",
                "Communication",
                "Leadership",
                "Other"
            ],
            "reqd": True
        },
        {
            "fieldname": "sentiment",
            "fieldtype": "Select",
            "label": "Sentiment",
            "description": "Overall tone of the response",
            "options": [
                "Positive",
                "Neutral",
                "Negative",
                "Mixed"
            ],
            "reqd": True
        },
        {
            "fieldname": "source_method",
            "fieldtype": "Select",
            "label": "Source/Method",
            "description": "How was this feedback obtained?",
            "options": [
                "Survey",
                "Interview",
                "Focus Group",
                "Community Meeting",
                "Public Participation",
                "Grievance/Complaint",
                "Field Engagement",
                "Email",
                "Digital Platform",
                "Facilitator Observation",
                "Other"
            ],
            "reqd": True
        },
        {
            "fieldname": "status",
            "fieldtype": "Select",
            "label": "Status",
            "description": "Has this response been reviewed and addressed?",
            "options": [
                "Open",
                "Reviewed",
                "Closed"
            ],
            "default": "Open",
            "reqd": True
        },
        {
            "fieldname": "notes",
            "fieldtype": "Text Editor",
            "label": "Notes",
            "description": "Practitioner notes, follow-up actions, or context",
            "reqd": False
        },
        {
            "fieldname": "created_by_user",
            "fieldtype": "Data",
            "read_only": True,
            "label": "Recorded By"
        },
        {
            "fieldname": "created_timestamp",
            "fieldtype": "Datetime",
            "read_only": True,
            "label": "Recorded Date"
        }
    ]
}
```

### Key Design Decisions

**Optional Linking:**
- Stakeholder, stakeholder_group, geographic_area, intervention, objective are all optional
- A response can stand alone OR be linked to context
- Practitioners can add context gradually

**Response Type vs Sentiment:**
- **Response Type** = What kind of communication is it? (Question, Concern, Suggestion, etc.)
- **Sentiment** = What's the emotional tone? (Positive, Negative, Neutral, Mixed)
- Example: "Please provide the relocation timetable" = Question (type) + Neutral (sentiment)
- Example: "I don't understand eligibility" = Concern (type) + Negative (sentiment)

**Theme Classification:**
- Simple, controlled list (not free-text to enable filtering)
- Flexible enough for common topics
- "Other" available for edge cases
- Can be expanded as patterns emerge

---

## Phase 5 Distinction: Two Evidence Streams

### Quantitative Evidence (Phase 3)

```
Evidence Record
├─ Type: Survey
├─ Source: Survey Team
├─ Collection Date: July 2026
├─ Finding: 68% understanding
└─ Status: Verified
```

### Qualitative Evidence (Phase 5)

```
Stakeholder Response
├─ Source: Community Meeting
├─ Date: July 15, 2026
├─ Feedback: "We understand relocation, but documentation unclear"
├─ Type: Concern
├─ Theme: Documentation
├─ Sentiment: Negative
└─ Status: Reviewed
```

### Together They Tell a Complete Story

```
Objective: Increase understanding of relocation process

Measured Outcome: 68% understanding ✅ (Phase 2 + 3)

Stakeholder Responses:
  - 146 total responses
  - 51 negative (35%)
  - Top concerns:
    * Documentation (21)
    * Eligibility (27)
    * Process clarity (38)

Practitioner Insight:
"68% say they understand, but qualitative feedback shows
confusion about specifics: documentation requirements,
eligibility criteria, and process clarity remain gaps."
```

---

## Phase 5 Response Classifications

### Response Type (8 + Other)

| Type | Purpose | Example |
|------|---------|----------|
| **Question** | Seeking information | "When does relocation start?" |
| **Suggestion** | Proposing improvement | "Host Q&A sessions for residents" |
| **Concern** | Expressing worry/uncertainty | "I'm worried about losing my home" |
| **Complaint** | Expressing dissatisfaction | "Communication was very poor" |
| **Positive Feedback** | Expressing satisfaction | "Great job explaining the process" |
| **Negative Feedback** | Expressing dissatisfaction | "This whole thing is a mess" |
| **Request for Information** | Asking for specific data | "Can you send the eligibility list?" |
| **Request for Assistance** | Asking for help | "I need help filling out the form" |
| **Other** | Catch-all | (flexible) |

### Theme (13 + Other)

| Theme | Purpose | Examples |
|-------|---------|----------|
| **Programme Understanding** | General comprehension | "I don't understand the whole programme" |
| **Eligibility** | Qualification criteria | "Am I eligible for relocation support?" |
| **Process** | Steps/procedures | "What's the relocation process?" |
| **Service Access** | Reaching/using services | "How do I submit my application?" |
| **Trust** | Confidence/credibility | "Do we believe the government?" |
| **Participation** | Involvement/voice | "Will our community have a say?" |
| **Timing** | Schedule/urgency | "When will this happen?" |
| **Documentation** | Required papers/records | "What documents do I need?" |
| **Compensation** | Payment/benefits | "Will we get compensation?" |
| **Relocation** | Moving/resettlement | "Where will we be relocated to?" |
| **Communication** | Information flow | "Why wasn't this communicated better?" |
| **Leadership** | Decision-makers/authority | "Who's making these decisions?" |
| **Other** | Catch-all | (flexible) |

### Sentiment (4)

| Sentiment | Meaning |
|-----------|----------|
| **Positive** | Satisfied, supportive, optimistic |
| **Neutral** | Factual, informational, neither good nor bad |
| **Negative** | Dissatisfied, critical, worried |
| **Mixed** | Contains both positive and negative elements |

---

## Phase 5 Backend Services

### Service: `stakeholder_response_analysis.py`

**Responsibility:** Capture, retrieve, and analyze stakeholder responses

**Key Functions:**

```python
def create_stakeholder_response(
    response_text: str,
    response_date: str,
    response_type: str,
    theme: str,
    sentiment: str,
    source_method: str,
    stakeholder_group: str = None,
    geographic_area: str = None,
    intervention: str = None,
    objective: str = None,
    notes: str = None
) -> dict:
    """
    Create a new stakeholder response record.
    
    Returns: {"status": "success", "response_id": "..."}
    """
    pass

def get_responses_for_objective(
    objective_name: str,
    filters: dict = None  # {"sentiment": "Negative", "theme": "Documentation"}
) -> list:
    """
    Get all responses linked to an objective.
    
    Returns:
    [
        {
            "response_text": "...",
            "response_date": "2026-07-15",
            "response_type": "Concern",
            "theme": "Documentation",
            "sentiment": "Negative",
            "stakeholder_group": "Affected Residents",
            "geographic_area": "Ward 12",
            "source_method": "Community Meeting"
        },
        ...
    ]
    """
    pass

def get_response_summary(
    objective_name: str = None,
    intervention_name: str = None,
    date_range: tuple = None  # (start_date, end_date)
) -> dict:
    """
    Get high-level summary of responses.
    
    Returns:
    {
        "total_responses": 146,
        "by_sentiment": {
            "positive": 42,
            "neutral": 37,
            "negative": 51,
            "mixed": 16
        },
        "by_response_type": {
            "question": 38,
            "concern": 45,
            "suggestion": 12,
            ...
        },
        "by_theme": {
            "documentation": 21,
            "eligibility": 27,
            "process": 38,
            "trust": 19,
            "service_access": 17,
            ...
        }
    }
    """
    pass

def get_theme_analysis(
    theme: str,
    objective_name: str = None
) -> dict:
    """
    Analyze all responses for a specific theme.
    
    Returns:
    {
        "theme": "Documentation",
        "total_responses": 21,
        "by_sentiment": {"positive": 2, "neutral": 3, "negative": 16, "mixed": 0},
        "by_stakeholder_group": {
            "Affected Residents": 18,
            "Community Leaders": 3
        },
        "by_geographic_area": {
            "Ward 1": 3,
            "Ward 4": 12,
            "Ward 2": 4,
            "Ward 3": 2
        },
        "sample_responses": [
            "Need to know what documents to submit",
            "Was never told what paperwork we need",
            ...
        ]
    }
    """
    pass

def get_response_trend(
    objective_name: str = None,
    intervention_name: str = None,
    by_sentiment: bool = False
) -> dict:
    """
    Get responses over time to detect trends.
    
    Returns:
    {
        "monthly_trend": [
            {"month": "2026-05", "total": 12, "negative": 3},
            {"month": "2026-06", "total": 21, "negative": 6},
            {"month": "2026-07", "total": 37, "negative": 17},
            {"month": "2026-08", "total": 49, "negative": 24},
        ],
        "interpretation": "Responses increasing. Negative sentiment increasing faster."
    }
    """
    pass

def get_discrepancies(
    objective_name: str
) -> dict:
    """
    Compare measured outcome with stakeholder feedback.
    Identify where quantitative and qualitative data diverge.
    
    Returns:
    {
        "objective": "Increase understanding of relocation",
        "measured_outcome": {
            "value": 68,
            "unit": "%",
            "status": "On Track"
        },
        "stakeholder_responses": {
            "total": 146,
            "negative_percent": 35,
            "primary_concerns": ["Documentation", "Eligibility", "Process"]
        },
        "discrepancy_assessment": {
            "exists": True,
            "interpretation": "Measured understanding high, but qualitative feedback shows confusion about specifics.",
            "recommendation": "Investigate gap: understanding vs. confidence in details."
        }
    }
    """
    pass

def filter_responses(
    filters: dict = None  # {"sentiment": "Negative", "theme": "Documentation", "geographic_area": "Ward 4"}
) -> list:
    """
    Search responses by multiple criteria.
    
    Returns: List of matching response records
    """
    pass

def update_response_status(
    response_id: str,
    status: str,  # "Open" | "Reviewed" | "Closed"
    notes: str = None
) -> dict:
    """
    Change response status and add notes.
    
    Returns: {"status": "success", "updated_record": {...}}
    """
    pass
```

### Service: `stakeholder_response_api.py`

**Responsibility:** REST API endpoints for response capture and analysis

**Endpoints:**

```
POST /api/method/srm_core.services.stakeholder_response_api.create_response
    Payload: Response data
    → Creates new response record

GET /api/method/srm_core.services.stakeholder_response_api.get_responses_for_objective
    ?objective_name=[name]&sentiment=[type]&theme=[theme]
    → Get filtered responses for objective

GET /api/method/srm_core.services.stakeholder_response_api.get_response_summary
    ?objective_name=[name]&date_range=[start,end]
    → Get high-level summary (counts by sentiment, type, theme)

GET /api/method/srm_core.services.stakeholder_response_api.get_theme_analysis
    ?theme=[name]&objective_name=[name]
    → Get detailed analysis for specific theme

GET /api/method/srm_core.services.stakeholder_response_api.get_response_trend
    ?objective_name=[name]&by_sentiment=[true/false]
    → Get monthly trend of responses

GET /api/method/srm_core.services.stakeholder_response_api.get_discrepancies
    ?objective_name=[name]
    → Compare measured outcome vs. stakeholder feedback

GET /api/method/srm_core.services.stakeholder_response_api.filter_responses
    ?sentiment=[type]&theme=[theme]&geographic_area=[area]
    → Search/filter responses by multiple criteria

PUT /api/method/srm_core.services.stakeholder_response_api.update_response_status
    ?response_id=[id]&status=[Open/Reviewed/Closed]&notes=[text]
    → Update response status and notes
```

---

## Phase 5 Frontend Components

### 1. **Stakeholder Response Capture Form**
**File:** `src/components/Phase5/StakeholderResponseForm.tsx`

**Features:**
- Text area for response (required)
- Date picker (required)
- Response type dropdown (required)
- Theme dropdown (required)
- Sentiment selector (required)
- Source/method dropdown (required)
- Optional: Stakeholder selector
- Optional: Stakeholder group selector
- Optional: Geographic area selector
- Optional: Intervention selector
- Optional: Objective selector
- Optional: Notes field
- Save button (creates record)

**UX Design Principle:** Practitioner can capture response in seconds

### 2. **Response Summary Card**
**File:** `src/components/Phase5/ResponseSummaryCard.tsx`

**Shows:**
- Total responses (count)
- Breakdown by sentiment (positive/neutral/negative/mixed)
- Top 5 themes (with counts)
- Top 5 response types (with counts)
- Links to drill-down

### 3. **Response Table Component**
**File:** `src/components/Phase5/ResponseTable.tsx`

**Features:**
- List all responses (with pagination)
- Columns: Date, Response (truncated), Type, Theme, Sentiment, Stakeholder Group, Area, Status
- Sortable by any column
- Filterable by:
  - Sentiment
  - Theme
  - Response type
  - Stakeholder group
  - Geographic area
  - Date range
  - Status
- Click row to view full response
- Bulk update status (Open → Reviewed → Closed)

### 4. **Response Detail View**
**File:** `src/components/Phase5/ResponseDetailView.tsx`

**Shows:**
- Full response text
- Response date
- All classifications (type, theme, sentiment, source)
- Linked stakeholder/group/area/objective/intervention
- Current status
- Practitioner notes
- Related responses (same theme or stakeholder group)
- Status change buttons
- Edit notes button

### 5. **Theme Analysis Card**
**File:** `src/components/Phase5/ThemeAnalysisCard.tsx`

**Shows:**
- Selected theme name
- Total responses for that theme
- Sentiment breakdown (pie or bar chart)
- Geographic distribution
- Stakeholder group distribution
- Sample response quotes
- Trend over time (line chart)

### 6. **Discrepancy Alert Component**
**File:** `src/components/Phase5/DiscrepancyAlert.tsx`

**Shows:**
- Objective name
- Measured outcome (value, target, status)
- Stakeholder response summary (total, sentiment breakdown)
- Primary concerns/themes
- Alert: "Gap detected between quantitative and qualitative data"
- Interpretation
- Recommendations

### 7. **Response Trend Chart**
**File:** `src/components/Phase5/ResponseTrendChart.tsx`

**Shows:**
- Monthly trend line
- Optional: Overlay negative sentiment trend
- Annotations for key events
- Y-axis: Number of responses
- X-axis: Time (months)
- Tooltip with exact counts

### 8. **Quick Capture Modal**
**File:** `src/components/Phase5/QuickCaptureModal.tsx`

**Purpose:** Capture response from intervention or objective page without navigation

**Features:**
- Minimal form (response text + required fields)
- Pre-populate intervention/objective if opened from that context
- Submit → Record created → Clear form for next entry
- Ideal for rapid data entry at community meetings

---

## Phase 5 Practitioner Workflow

### Workflow 1: Capture Response During Community Meeting

```
1. Open QuickCaptureModal from Intervention page
2. Paste/type stakeholder feedback
3. Select date (defaults to today)
4. Select response type (Concern)
5. Select theme (Documentation)
6. Select sentiment (Negative)
7. Select source (Community Meeting)
8. Save → Record created
9. Next response: Click "Clear form"
10. Repeat steps 2-9 (10-15 responses in one session)
```

**Time per response:** ~20-30 seconds

### Workflow 2: Link Response to Objective

```
1. Open Communication Objective page
2. Scroll to "Stakeholder Responses" section
3. See:
   - Summary card (total, sentiment breakdown, top themes)
   - Response table (all responses for this objective)
   - Discrepancy alert (if measured outcome conflicts with feedback)
4. Click "Add Response" → Populate intervention/objective automatically
5. Fill in response details
6. Save → Response linked
```

### Workflow 3: Analyze Theme Across Programme

```
1. Open "Responses" dashboard
2. See overall summary (all responses, all interventions)
3. Click theme: "Documentation" → Theme analysis card opens
4. See:
   - 21 responses about documentation
   - 16 negative, 3 neutral, 2 positive
   - Geographic distribution (12 in Ward 4, 3 in Ward 1, etc.)
   - Stakeholder group distribution
   - Sample quotes
   - Trend over time
5. Drill down: "View all documentation responses" → Filtered table
6. Filter further by Ward → See documentation concerns specific to Ward 4
```

### Workflow 4: Review Discrepancy

```
1. Open Objective: "Increase understanding of relocation"
2. See:
   - Measured outcome: 68% understanding ✓ On Track
   - Stakeholder responses: 146 total
   - Sentiment: 42 positive, 37 neutral, 51 negative, 16 mixed
   - Top concerns: Documentation (21), Eligibility (27), Process (38)
   - ⚠️ DISCREPANCY: High measured understanding, but 35% negative feedback
3. Click "View discrepancy details"
4. See interpretation: "Respondents say they understand concept, but lack confidence in specifics."
5. Recommendation: "Investigate what 'understanding' means vs. confidence in details."
6. Take action: Plan documentation/eligibility session
```

---

## Phase 5 Example Scenarios

### Scenario 1: Community Meeting Feedback

**Context:** Community meeting in Ward 12, July 15, 2026

**Feedback:** "We understand that relocation is planned, but we don't know what documents we need to submit."

**Recorded as:**
```
Response Text:       "We understand that relocation is planned, but we don't know what documents we need to submit."
Response Date:       2026-07-15
Response Type:       Concern
Theme:               Documentation
Sentiment:           Negative (understands concept, but frustrated about lack of clarity)
Stakeholder Group:   Affected Residents
Geographic Area:     Ward 12
Intervention:        Ward 12 Housing Awareness Campaign
Objective:           Increase understanding of relocation process
Source:              Community Meeting
Status:              Open → Reviewed (after practitioner acknowledges)
Notes:               "Second time hearing this concern. Need urgent documentation guide."
```

### Scenario 2: Focus Group Discussion

**Context:** Focus group with youth, July 20, 2026

**Feedback:** "This relocation thing doesn't affect us. We're leaving the city anyway."

**Recorded as:**
```
Response Text:       "This relocation thing doesn't affect us. We're leaving the city anyway."
Response Date:       2026-07-20
Response Type:       Negative Feedback
Theme:               Participation
Sentiment:           Negative
Stakeholder Group:   Youth (18-25)
Geographic Area:     Ward 4
Intervention:        Ward 12 Housing Awareness Campaign
Objective:           Increase engagement with relocation process
Source:              Focus Group
Status:              Open
Notes:               "Youth disengagement. Consider youth-specific messaging."
```

### Scenario 3: Positive Feedback

**Context:** Email from community leader, July 18, 2026

**Feedback:** "Thank you for the clear explanations at the meeting. Our community is ready to support the process."

**Recorded as:**
```
Response Text:       "Thank you for the clear explanations at the meeting. Our community is ready to support the process."
Response Date:       2026-07-18
Response Type:       Positive Feedback
Theme:               Communication (or Trust, or Participation)
Sentiment:           Positive
Stakeholder Group:   Community Leaders
Geographic Area:     Ward 1
Intervention:        Ward 12 Housing Awareness Campaign
Objective:           Increase engagement with relocation process
Source:              Email
Status:              Reviewed
Notes:               "Key ally. Consider as resource for Ward 4 messaging."
```

---

## Phase 5 Response Summary Example

### Dashboard View

```
STAKEHOLDER RESPONSE OVERVIEW

Programme: Ward 12 Housing Awareness Campaign
Date Range: May 1 - Aug 31, 2026

TOTAL RESPONSES: 146

BY SENTIMENT:
  Positive:     42  (29%)  ■■■■■■■□□□
  Neutral:      37  (25%)  ■■■■■□□□□□
  Negative:     51  (35%)  ■■■■■■■□□□
  Mixed:        16  (11%)  ■■□□□□□□□□

BY RESPONSE TYPE:
  Question:                  38
  Concern:                   45
  Suggestion:                12
  Positive Feedback:         21
  Negative Feedback:         19
  Request for Information:   28
  Request for Assistance:     9
  Complaint:                  8
  Other:                      6

TOP THEMES:
  Theme                  Responses    Sentiment
  Process                     38      ■ (24% negative)
  Eligibility                 27      ■■ (41% negative)
  Documentation              21      ■■ (48% negative)
  Trust                       19      ■ (26% negative)
  Service Access             17      ■ (29% negative)

TRENDS:
  May:      12 responses   (3 negative)
  Jun:      21 responses   (6 negative)
  Jul:      37 responses   (17 negative)
  Aug:      49 responses   (24 negative)
  
  → Responses increasing 20% month-on-month
  → Negative sentiment increasing 40% month-on-month ⚠️

LOCATION SUMMARY:
  Ward 1:     18 responses  (2 negative)
  Ward 2:     31 responses  (9 negative)
  Ward 3:     38 responses  (14 negative)
  Ward 4:     59 responses  (26 negative)  ⚠️ 44% negative

STAKEHOLDER GROUP SUMMARY:
  Community Leaders:    22 responses  (3 negative)
  Affected Residents:   89 responses  (35 negative)
  Youth (18-25):        21 responses  (14 negative)  ⚠️ 67% negative
  Other:                14 responses  (3 negative)
```

---

## Phase 5 Linking to Phase 4

### Extended Disaggregated View

**Previous (Phase 4):**
```
Ward 4
├─ Understanding: 43%
├─ Geographic breakdown
└─ Stakeholder breakdown
```

**Enhanced (Phase 4 + 5):**
```
Ward 4
├─ Understanding: 43% (measured)
├─ 59 stakeholder responses
│  ├─ 26 negative (44%)
│  ├─ Top themes:
│  │  ├─ Documentation: 16 responses
│  │  ├─ Eligibility: 12 responses
│  │  └─ Process: 14 responses
│  └─ Trend: 24 negative responses in Aug (up from 3 in May)
└─ Interpretation: "Measured understanding only 43%, and qualitative
                   feedback shows specific concerns about documentation
                   and eligibility. Negative sentiment accelerating."
```

---

## Phase 5 Connection to Measurement

### Outcome Objective Page (Enhanced)

```
OBJECTIVE: Increase understanding of relocation process

MEASURED OUTCOME:
  Current:   68%
  Target:    75%
  Status:    On Track

EVIDENCE LINKS (Phase 3):
  Survey (July):    68% understanding (verified)
  Focus Group:      General comprehension confirmed
  Interviews:       7/10 can explain process

STAKEHOLDER RESPONSES (Phase 5): 146 responses
  Sentiment:        35% negative (51 responses)
  Primary Concerns:
    - Documentation: 21 responses
    - Eligibility: 27 responses
    - Process clarity: 38 responses

DISCREPANCY ANALYSIS:
  ⚠️ Gap detected
  Measured understanding (68%) vs. Confidence in details (low)
  
  Interpretation:
  Respondents can say "yes, I understand relocation is happening"
  but cannot confidently answer:
    - What documents do I need?
    - Am I eligible?
    - What are the exact steps?
  
  Recommendation:
  Surface-level understanding exists.
  Deep understanding requires targeted documentation/eligibility support.
```

---

## Phase 5 Acceptance Criteria

| # | Criterion | Owner |
|---|-----------|-------|
| 1 | Stakeholder Response DocType created | Backend |
| 2 | All required fields present | Backend |
| 3 | Response Type controlled values defined | Backend |
| 4 | Theme controlled values defined | Backend |
| 5 | Sentiment (4 options) defined | Backend |
| 6 | Source/Method controlled values defined | Backend |
| 7 | Status workflow (Open/Reviewed/Closed) works | Backend |
| 8 | Response can link to Stakeholder (optional) | Backend |
| 9 | Response can link to Stakeholder Group (optional) | Backend |
| 10 | Response can link to Geographic Area | Backend |
| 11 | Response can link to Intervention | Backend |
| 12 | Response can link to Objective | Backend |
| 13 | Response creation API endpoint works | Backend |
| 14 | Response retrieval API endpoint works | Backend |
| 15 | Response summary API endpoint works | Backend |
| 16 | Theme analysis API endpoint works | Backend |
| 17 | Response trend API endpoint works | Backend |
| 18 | Discrepancy detection API endpoint works | Backend |
| 19 | Response filtering API endpoint works | Backend |
| 20 | Response status update API endpoint works | Backend |
| 21 | Capture form component renders | Frontend |
| 22 | Summary card component displays correctly | Frontend |
| 23 | Response table component displays correctly | Frontend |
| 24 | Response detail view displays correctly | Frontend |
| 25 | Theme analysis card displays correctly | Frontend |
| 26 | Discrepancy alert displays correctly | Frontend |
| 27 | Response trend chart displays correctly | Frontend |
| 28 | Quick capture modal works | Frontend |
| 29 | Filters work (by sentiment, theme, area, etc.) | Frontend |
| 30 | All filtering combinations work | Frontend |
| 31 | Response capture < 30 seconds per entry | Frontend |
| 32 | Mobile responsive (form, table, charts) | Frontend |
| 33 | No AI/NLP/sentiment analysis included | Both |
| 34 | Existing Stakeholder/Geographic Area structures reused | Both |
| 35 | Phases 1-4 architecture remains intact | Both |
| 36 | End-to-end workflow works (capture → classify → analyze) | Both |
| 37 | Discrepancy between measurement and feedback visible | Both |
| 38 | All tests passing (unit + integration + E2E) | Both |
| 39 | Documentation complete | Both |
| 40 | Example scenarios work | Both |

---

## What Phase 5 Does NOT Include

❌ **Deliberately Excluded (Phase 6+):**
- AI sentiment analysis
- Automated theme extraction
- NLP processing
- Natural language understanding
- Predictive sentiment modeling
- Automated recommendations
- Early Warning Engine
- Anomaly detection
- Root-cause analysis
- Contribution analysis
- Attribution modeling
- Advanced demographic profiling
- Automated narratives

✅ **Phase 5 Focus:** Clean, structured stakeholder-response data captured manually by practitioners.

---

## Phase 5 Integration with Phases 1-4

```
PHASE 1: What?
  Intervention → Objective → Indicator
  
PHASE 2: Whether?
  Measurement → Progress → Status
  
PHASE 3: How?
  Evidence → Verification → Attachment
  
PHASE 4: Who & Where?
  Disaggregation by stakeholder/geography
  
PHASE 5: What are they saying?  [NEW]
  Stakeholder Response → Classification → Theme → Discrepancy Detection
```

**The layers now tell a complete story:**

```
Intervention: Ward 12 Housing Awareness
   ↓
Objective: Increase understanding of relocation
   ↓
Measured: 68% understanding (Phase 2)
   ↓
Evidence: Survey verified (Phase 3)
   ↓
Disaggregated: 43% in Ward 4, 51% among youth (Phase 4)
   ↓
Stakeholder Feedback: 51 negative responses, top concerns
                      about documentation & eligibility (Phase 5)
   ↓
Insight: "Broad understanding exists, but lacks depth.
         Specific concerns about documentation and eligibility.
         Ward 4 and youth disproportionately affected.
         Issue appears to be growing (trend worsening)."
```

---

## Phase 5 Implementation Timeline

**Backend (Copilot):** 2-3 days
- Create Stakeholder Response DocType
- Build analysis services
- Create API endpoints
- Write unit tests

**Frontend (Cursor):** 2-3 days
- Build response capture form
- Build summary & analysis components
- Implement filtering/search
- Write integration tests

**Total:** 4-6 days (parallel frontend/backend)

---

## Support & Resources

**Documentation:**
- `docs/PHASE_5_STAKEHOLDER_RESPONSE_PLAN.md` - This document
- `docs/MASTER_ROADMAP_ALL_PHASES.md` - Complete 5-phase vision
- Previous phase guides (1-4)

**TrustLedger Evolution:**
- Phase 1: Framework (What?)
- Phase 2: Measurement (Whether?)
- Phase 3: Evidence (How?)
- Phase 4: Segmentation (Who & Where?)
- **Phase 5: Voice (What are they saying?)**
- Phase 6+: Intelligence (Why? How much? Confidence?)

---

*Phase 5 architecture prepared by: GitHub Copilot*  
*Date: September 2, 2026*  
*Branch: feature/phase-5-stakeholder-response*  
*Status: Ready for implementation*
