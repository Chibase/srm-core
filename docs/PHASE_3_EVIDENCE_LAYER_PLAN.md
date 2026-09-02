# Phase 3: Evidence Layer - Architecture & Planning

## Overview

Phase 3 establishes the evidence foundation for TrustLedger's impact measurements.

**Core Question:** What evidence supports the outcome we are reporting?

**Goal:** Create an audit trail connecting outcomes back to their sources.

```
Communication Intervention
          ↓
Communication Objective
          ↓
Impact Indicator
          ↓
Measurement Record
          ↓
Evidence Record  ← NEW (Phase 3)
          ↓
Attachments (Files)
```

---

## Phase 3 Scope (4 Capabilities)

### 1. Measurement Method

Every measurement identifies **how** it was obtained.

**Controlled Values:**
- Survey
- Interview
- Focus Group
- Observation
- Attendance Register
- Administrative Data
- Field Verification
- Digital Analytics
- Document Review
- Other

**Where it lives:** `Measurement Record.measurement_method` (new field)

### 2. Evidence Record

A new DocType that captures supporting evidence for a measurement.

**Schema:**

| Field | Type | Purpose |
|-------|------|----------|
| `evidence_name` | Data | Name/description of evidence |
| `measurement` | Link → Measurement Record | Which measurement this supports |
| `evidence_type` | Select | Method used (Survey, Interview, etc) |
| `collection_date` | Date | When evidence was collected |
| `source` | Data | Where it came from (e.g., "Ward 12 household survey") |
| `description` | Text | Brief explanation |
| `verification_status` | Select | Unverified / Reviewed / Verified |
| `notes` | Small Text | Additional info |
| `attachments` | Frappe Attachment | Supporting files |

**Key Points:**
- One measurement can have **multiple** evidence records
- Evidence is linked ONE-to-ONE with Measurement Record
- Attachments use Frappe's built-in attachment system (no custom file storage)

### 3. Evidence Status

**3 simple states (NOT a quality score):**

1. **Unverified**
   - Evidence uploaded/recorded but not reviewed
   - Initial state

2. **Reviewed**
   - A practitioner examined the evidence
   - Checked for completeness, relevance, quality
   - May request changes/clarification

3. **Verified**
   - Responsible person confirmed evidence is suitable for measurement
   - Evidence "locked in" as supporting the measurement
   - Can still update notes, but status signals acceptance

**Transitions:**
```
Unverified → (practitioner reviews) → Reviewed → (responsible approves) → Verified
           ↑                                                            ↓
           └─────────────────────── (can revert) ──────────────────────┘
```

### 4. Evidence-to-Measurement Relationship

**One Measurement → Multiple Evidence Records**

Example:
```
Measurement
├─ Value: 68%
├─ Date: July 2026
├─ Objective: Understanding of relocation process
│
└─ Supporting Evidence:
   ├─ Evidence 1: Household Survey
   │  ├─ Type: Survey
   │  ├─ Source: Ward 12 household survey
   │  ├─ Date: July 10, 2026
   │  ├─ Status: Verified
   │  └─ Attachment: survey_results.pdf
   │
   ├─ Evidence 2: Focus Group
   │  ├─ Type: Focus Group
   │  ├─ Source: Resident focus group meeting
   │  ├─ Date: July 15, 2026
   │  ├─ Status: Reviewed
   │  └─ Attachment: focus_group_notes.docx
   │
   └─ Evidence 3: Field Verification
      ├─ Type: Field Verification
      ├─ Source: Verification team
      ├─ Date: July 20, 2026
      ├─ Status: Verified
      └─ Attachment: verification_report.pdf
```

---

## Phase 3 DocType Specification

### DocType: `Communication Evidence`

**Important:** Before creating, Cursor must check if TrustLedger already has a generic `Evidence`, `Supporting Document`, or equivalent DocType. If it does, **reuse it** rather than creating a duplicate.

**Field Definitions:**

```python
{
    "doctype": "Communication Evidence",
    "module": "SRM Core",
    "autoname": "autoincrement",  # Or naming convention
    "fields": [
        {
            "fieldname": "evidence_name",
            "fieldtype": "Data",
            "label": "Evidence Name",
            "required": True,
            "description": "Name or description of the evidence"
        },
        {
            "fieldname": "measurement",
            "fieldtype": "Link",
            "options": "Measurement Record",
            "label": "Measurement",
            "required": True,
            "description": "The measurement this evidence supports"
        },
        {
            "fieldname": "evidence_type",
            "fieldtype": "Select",
            "options": "Survey\nInterview\nFocus Group\nObservation\nAttendance Register\nAdministrative Data\nField Verification\nDigital Analytics\nDocument Review\nOther",
            "label": "Evidence Type",
            "required": True,
            "description": "How the evidence was collected"
        },
        {
            "fieldname": "collection_date",
            "fieldtype": "Date",
            "label": "Collection Date",
            "required": True,
            "description": "When the evidence was collected"
        },
        {
            "fieldname": "source",
            "fieldtype": "Data",
            "label": "Source",
            "required": True,
            "description": "Where the evidence came from (e.g., 'Ward 12 household survey')"
        },
        {
            "fieldname": "description",
            "fieldtype": "Text",
            "label": "Description",
            "description": "Brief explanation of the evidence"
        },
        {
            "fieldname": "verification_status",
            "fieldtype": "Select",
            "options": "Unverified\nReviewed\nVerified",
            "label": "Verification Status",
            "default": "Unverified",
            "required": True,
            "description": "Evidence review status"
        },
        {
            "fieldname": "notes",
            "fieldtype": "Small Text",
            "label": "Notes",
            "description": "Additional information or reviewer comments"
        },
        {
            "fieldname": "created",
            "fieldtype": "Datetime",
            "label": "Created",
            "read_only": True
        },
        {
            "fieldname": "modified",
            "fieldtype": "Datetime",
            "label": "Modified",
            "read_only": True
        }
    ],
    "permissions": [
        {
            "role": "System Manager",
            "perm_type": "create",
            "read": True,
            "write": True,
            "create": True,
            "delete": True,
            "submit": False,
            "report": True,
            "share": True,
            "export": True
        },
        {
            "role": "SRM Admin",
            "perm_type": "create",
            "read": True,
            "write": True,
            "create": True,
            "delete": False,
            "submit": False,
            "report": True
        },
        {
            "role": "SRM Analyst",
            "perm_type": "create",
            "read": True,
            "write": True,
            "create": True,
            "delete": False,
            "report": True
        },
        {
            "role": "SRM Lead",
            "perm_type": "create",
            "read": True,
            "write": False,
            "create": False,
            "report": True
        },
        {
            "role": "SRM Viewer",
            "perm_type": "create",
            "read": True,
            "write": False,
            "report": True
        }
    ]
}
```

**Attachments:** Use Frappe's built-in attachment system:
- Practitioners upload files via standard Frappe file attachment UI
- System stores files with reference to Communication Evidence document
- No custom file management code

---

## Phase 3 Workflow

### Step 1: Create Intervention
```
Communication Intervention
├─ Name: Ward 12 Housing Awareness Campaign
├─ Type: Awareness Campaign
├─ Status: Active
```

### Step 2: Define Objective
```
Communication Objective
├─ Name: Increase residents' understanding of relocation
├─ Intervention: [from Step 1]
├─ Outcome Type: Understanding
├─ Baseline: 32%
├─ Target: 75%
```

### Step 3: Define Indicator
```
Impact Indicator
├─ Name: % Residents understanding relocation process
├─ Type: Percentage
├─ Baseline: 32%
├─ Target: 75%
```

### Step 4: Capture Measurement
```
Measurement Record  ← NEW in Phase 3
├─ Indicator: % Residents understanding relocation process
├─ Date: July 2026
├─ Value: 68%
├─ Measurement Method: Survey  ← NEW field
```

### Step 5: Attach/Record Evidence
```
Communication Evidence  ← NEW DocType
├─ Measurement: [from Step 4]
├─ Evidence Type: Survey
├─ Collection Date: July 10, 2026
├─ Source: Ward 12 household survey
├─ Description: 350 residents surveyed on understanding
├─ Status: Unverified
├─ Attachments: [survey_report.pdf, data_analysis.xlsx]
```

### Step 6: Review Evidence
```
Practitioner reviews evidence:
├─ Opens evidence record
├─ Reviews attachments
├─ Adds reviewer notes
├─ Changes status: Unverified → Reviewed
```

### Step 7: Verify Evidence
```
Responsible person verifies:
├─ Opens evidence record
├─ Confirms evidence is suitable
├─ May add verification notes
├─ Changes status: Reviewed → Verified
└─ Evidence now "locked in" as supporting measurement
```

### Step 8: View Outcome + Evidence
```
When practitioner views measurement:

Understanding of relocation process

Baseline: 32%
Current: 68%
Target: 75%
Status: On Track

Measurement Date: July 2026
Measurement Method: Survey

┌─────────────────────────────────────┐
│ SUPPORTING EVIDENCE                 │
├─────────────────────────────────────┤
│ Date    │ Type   │ Source  │ Status  │
├─────────┼────────┼─────────┼─────────┤
│ Jul 10  │ Survey │ Ward 12 │ Verified│
│ Jul 15  │ Focus  │ Resident│ Reviewed│
│ Jul 20  │ Field  │ Team    │ Verified│
└─────────────────────────────────────┘

[Click row to view full evidence record + attachments]
```

---

## Phase 3 Display Layer

### Measurement Record View (Enhanced)

Add new section to Measurement Record detail:

```
╔═══════════════════════════════════════════════╗
║ MEASUREMENT RECORD DETAIL                      ║
╠═══════════════════════════════════════════════╣
║                                               ║
║ Indicator: % Residents understanding...       ║
║ Value: 68%                                    ║
║ Date: July 2026                               ║
║                                               ║
║ ╔═════════════════════════════════════════╗   ║
║ ║ MEASUREMENT METHOD: Survey              ║   ║ ← NEW
║ ╚═════════════════════════════════════════╝   ║
║                                               ║
║ ╔═════════════════════════════════════════╗   ║
║ ║ SUPPORTING EVIDENCE                    ║   ║ ← NEW
║ ║                                         ║   ║
║ ║ [View Evidence] [Add Evidence]          ║   ║ ← NEW buttons
║ ║                                         ║   ║
║ ║ Evidence Records:                       ║   ║
║ ║ • Ward 12 household survey (Verified)   ║   ║
║ ║ • Resident focus group (Reviewed)       ║   ║
║ ║ • Field verification (Verified)         ║   ║
║ ║                                         ║   ║
║ ║ [Total: 3 evidence records]             ║   ║
║ ╚═════════════════════════════════════════╝   ║
║                                               ║
║ Notes: [measurement notes field]              ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

### Evidence Record Detail View

```
╔═══════════════════════════════════════════════╗
║ COMMUNICATION EVIDENCE                         ║
╠═══════════════════════════════════════════════╣
║                                               ║
║ Evidence Name: Ward 12 Household Survey       ║
║ Measurement: % Understanding (68%)            ║
║ Evidence Type: Survey                         ║
║ Collection Date: July 10, 2026                ║
║ Source: Ward 12 household survey              ║
║                                               ║
║ Description:                                  ║
║ 350 households surveyed during July 2026.     ║
║ Survey assessed understanding of relocation   ║
║ process, timeline, and eligibility criteria.  ║
║                                               ║
║ Verification Status: ⬤ Verified               ║
║ Status History:                               ║
║ • Unverified (Created: Jul 10, 2026)          ║
║ • Reviewed (Jul 15, 2026) - Reviewer notes    ║
║ • Verified (Jul 20, 2026) - Lead approval     ║
║                                               ║
║ Notes:                                        ║
║ Data quality good. Sample size adequate.      ║
║ Confirms 68% understanding across demographics║
║                                               ║
║ ╔═════════════════════════════════════════╗   ║
║ ║ ATTACHMENTS                             ║   ║
║ ║                                         ║   ║
║ ║ • survey_results.pdf (2.4 MB)           ║   ║
║ ║   Downloaded 20 times                   ║   ║
║ ║                                         ║   ║
║ ║ • survey_data.xlsx (500 KB)             ║   ║
║ ║   Downloaded 5 times                    ║   ║
║ ║                                         ║   ║
║ ║ • analysis_notes.docx (150 KB)          ║   ║
║ ║   Downloaded 3 times                    ║   ║
║ ║                                         ║   ║
║ ║ [+ Add File]                            ║   ║
║ ╚═════════════════════════════════════════╝   ║
║                                               ║
║ [Edit] [Change Status] [Delete]               ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

### Intervention Summary View (Enhanced)

```
╔═══════════════════════════════════════════════╗
║ WARD 12 HOUSING AWARENESS CAMPAIGN             ║
╠═══════════════════════════════════════════════╣
║                                               ║
║ OUTCOME: Understanding                        ║
║ Baseline: 32% → Current: 68% → Target: 75%    ║
║ Progress: 83.72% ✓ ON TRACK                   ║
║                                               ║
║ EVIDENCE SUMMARY:                             ║
║ • 3 evidence records (Verified: 2, Reviewed:1)║
║ • Last updated: 20 Jul 2026                   ║
║ • All measurement methods: Survey, Focus, Fld ║
║                                               ║
║ [View Full Evidence Trail] [Add Evidence]      ║
║                                               ║
╚═══════════════════════════════════════════════╝
```

---

## Phase 3 Backend Services

### Service: `evidence_management.py`

**Responsibility:** Create, retrieve, update evidence records

**Key Functions:**

```python
def create_evidence(
    evidence_name: str,
    measurement_name: str,
    evidence_type: str,
    collection_date: str,
    source: str,
    description: str = None,
    notes: str = None
) -> dict:
    """
    Create a new Communication Evidence record.
    Status automatically set to 'Unverified'.
    """
    pass

def get_evidence_for_measurement(
    measurement_name: str
) -> list:
    """
    Get all evidence records supporting a measurement.
    """
    pass

def change_evidence_status(
    evidence_name: str,
    new_status: str  # 'Unverified' | 'Reviewed' | 'Verified'
) -> dict:
    """
    Change verification status of evidence.
    Returns updated record.
    """
    pass

def get_evidence_summary(
    objective_name: str
) -> dict:
    """
    Get evidence summary for objective:
    - Total evidence records
    - Breakdown by status
    - Latest evidence date
    """
    pass

def validate_evidence_type(evidence_type: str) -> bool:
    """
    Validate evidence type is in controlled list.
    """
    pass

def get_evidence_types() -> list:
    """
    Get all valid evidence types.
    """
    pass
```

### Service: `evidence_api.py`

**Responsibility:** REST API endpoints for evidence operations

**Endpoints:**

```
POST /api/method/srm_core.services.evidence_api.create_evidence
  → Create new evidence record

GET /api/method/srm_core.services.evidence_api.get_evidence_for_measurement
  ?measurement_name=[name]
  → Get all evidence supporting a measurement

PUT /api/method/srm_core.services.evidence_api.change_evidence_status
  ?evidence_name=[name]&new_status=[status]
  → Change evidence verification status

GET /api/method/srm_core.services.evidence_api.get_evidence_summary
  ?objective_name=[name]
  → Get evidence overview for objective
```

---

## Phase 3 Measurement Record Enhancement

### New Field: `measurement_method`

Add to existing Measurement Record DocType:

```python
{
    "fieldname": "measurement_method",
    "fieldtype": "Select",
    "options": "Survey\nInterview\nFocus Group\nObservation\nAttendance Register\nAdministrative Data\nField Verification\nDigital Analytics\nDocument Review\nOther",
    "label": "Measurement Method",
    "description": "How this measurement was obtained",
    "insert_after": "measured_value"
}
```

**Migration Patch:**
- Retroactively set `measurement_method = 'Other'` for existing measurements
- Add field to Measurement Record form

---

## What We DO NOT Build (Phase 3)

✋ **Explicitly out of scope:**

- ❌ Evidence Quality Score (phase 4+)
- ❌ Evidence Confidence Index (phase 4+)
- ❌ AI evidence assessment (phase 4+)
- ❌ Automatic evidence verification (phase 4+)
- ❌ Attribution analysis (phase 4+)
- ❌ Contribution analysis (phase 4+)
- ❌ Causal inference (phase 4+)
- ❌ Predictive analytics (phase 4+)
- ❌ Advanced document intelligence (phase 4+)
- ❌ Policy impact modeling (phase 4+)
- ❌ Automated recommendations (phase 4+)

**Phase 3 Focus:** Build the evidence foundation. Practitioners manually verify evidence and make decisions.

---

## Phase 3 Acceptance Criteria

| # | Criterion | Owner |
|---|-----------|-------|
| 1 | Measurement Record has measurement_method field | Backend |
| 2 | Communication Evidence DocType created (or reused) | Backend |
| 3 | Evidence records link to measurements | Backend |
| 4 | Evidence type controlled values enforced | Backend |
| 5 | Evidence collection date captured | Backend |
| 6 | Evidence source field captures origin | Backend |
| 7 | Verification status workflow (3 states) | Backend |
| 8 | Frappe attachments integrated | Backend |
| 9 | Evidence API endpoints functional | Backend |
| 10 | Measurement detail view shows evidence | Frontend |
| 11 | Evidence detail view fully functional | Frontend |
| 12 | Evidence can be created via form | Frontend |
| 13 | Evidence status can be changed | Frontend |
| 14 | Evidence summary visible on objectives | Frontend |
| 15 | Attachments can be uploaded/downloaded | Frontend |
| 16 | No AI or confidence scoring | Both |
| 17 | No duplicate evidence architecture | Both |
| 18 | Phase 1 & 2 functionality intact | Both |
| 19 | Evidence visible in audit trail | Frontend |
| 20 | End-to-end workflow completes | Both |

---

## Phase 3 Example Scenario

**Scenario: Reporting the Ward 12 Understanding Measurement**

**Current State (After Phase 2):**
```
Communication Objective: Increase residents' understanding of relocation
Outcome Type: Understanding
Baseline: 32%
Current: 68%
Target: 75%
Progress: 83.72%
Status: On Track
```

**After Phase 3:**
```
(Everything above, PLUS:)

Measurement Date: July 2026
Measurement Method: Survey  ← NEW

Supporting Evidence (NEW SECTION):
1. Ward 12 Household Survey
   - Type: Survey
   - Collection Date: July 10, 2026
   - Source: Community Research Team
   - Status: Verified
   - Attachments:
     • survey_instrument.pdf
     • raw_data.xlsx
     • analysis_report.pdf
   - Verification Trail:
     • Created (Unverified): Jul 10
     • Reviewed by Analyst: Jul 15 ("Data quality good")
     • Verified by Lead: Jul 20 ("Confirmed 68%")

2. Resident Focus Group
   - Type: Focus Group
   - Collection Date: July 15, 2026
   - Source: Community Center Meeting
   - Status: Reviewed
   - Attachments:
     • focus_group_notes.docx
     • participant_list.pdf
   - Verification Trail:
     • Created (Unverified): Jul 15
     • Reviewed by Analyst: Jul 18 ("Aligns with survey findings")

3. Field Verification
   - Type: Field Verification
   - Collection Date: July 20, 2026
   - Source: Verification Team
   - Status: Verified
   - Attachments:
     • verification_report.pdf
   - Verification Trail:
     • Created (Unverified): Jul 20
     • Verified by Lead: Jul 22 ("Confirms survey data")
```

**Now when someone asks: "How do we know understanding is 68%?"**

Answer: Click the measurement → See evidence trail → Download supporting materials → Verify independently.

---

## Phase 3 Implementation Timeline

**Backend (Copilot):**
1. Create Communication Evidence DocType
2. Add measurement_method field to Measurement Record
3. Create evidence_management.py service
4. Create evidence_api.py with endpoints
5. Create migration patches
6. Write unit tests

**Frontend (Cursor):**
1. Build evidence create form
2. Build evidence detail view
3. Build evidence list/table component
4. Build evidence summary card
5. Integrate into measurement detail view
6. Add attachment upload/download
7. Add status change workflow
8. Write integration tests

---

## Phase 3 Dependencies & Tech Stack

**Backend:**
- Frappe framework (existing)
- Python (existing)
- SQLite/PostgreSQL (existing)
- Frappe's attachment system (existing, no new dependencies)

**Frontend:**
- React (existing)
- TypeScript (existing)
- Frappe REST API (existing)
- No new dependencies required

---

## Phase 3 Progression

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
├─ Status (On Track / Needs Attention / Off Track / No Data)
└─ Trend (Month-by-month measurements)
       ↓

PHASE 3: WHAT EVIDENCE SUPPORTS THE CHANGE?
├─ Measurement Method (Survey, Interview, etc)
├─ Evidence Record (linked to measurement)
├─ Evidence Type (Survey, Focus Group, etc)
├─ Collection Date
├─ Source (where it came from)
├─ Verification Status (Unverified / Reviewed / Verified)
├─ Supporting Attachments (files)
└─ Evidence Trail (who reviewed, when, notes)
```

---

## Next: Phase 4+

**Phase 4 capabilities (future):**
- Evidence confidence scoring
- Data quality assessment
- AI-powered evidence review
- Contribution analysis (multiple interventions → shared outcome)
- Attribution modeling
- Advanced analytics

**For now: Phase 3 is the foundation that makes Phase 4 possible.**

---

## Files to Create (Phase 3 Backend)

```
srm_core/
├── srm_core/
│   ├── doctype/
│   │   └── communication_evidence/  ← NEW DocType
│   │       ├── communication_evidence.py
│   │       ├── communication_evidence.json
│   │       └── communication_evidence.js
│   ├── services/
│   │   ├── evidence_management.py  ← NEW service
│   │   └── evidence_api.py  ← NEW API endpoints
│   └── tests/
│       ├── test_evidence_management.py  ← NEW tests
│       └── test_evidence_api.py  ← NEW tests
├── patches/
│   └── v1_3/
│       ├── __init__.py
│       ├── add_measurement_method_field.py  ← Adds field to existing DocType
│       └── seed_evidence_types.py  ← Seed controlled values
└── patches.txt  ← Updated registry
```

---

## Support & Resources

**Frappe Documentation:**
- DocType creation: https://frappeframework.com/docs/user/en/basics/doctypes
- Attachments: https://frappeframework.com/docs/user/en/file-attachment
- API: https://frappeframework.com/docs/user/en/using-the-rest-api

**TrustLedger Architecture:**
- Phase 1 Guide: `docs/PHASE_1_IMPLEMENTATION_GUIDE.md`
- Phase 2 Guide: `docs/PHASE_2_IMPLEMENTATION_GUIDE.md`
- This doc: Phase 3 Planning

---

## Next Steps

1. **Cursor finishes Phase 2 frontend** (in parallel)
2. **Copilot creates Phase 3 backend** (starts after Phase 2 merge)
3. **Cursor builds Phase 3 frontend** (after backend ready)
4. **Full system validation** (all 3 phases together)
5. **Handoff to production** (UAT and deployment)

---

**Phase 3 is designed to be the final piece of the evidence puzzle: connecting outcome claims back to their sources through a clear, traceable audit trail.**

*Prepared by: GitHub Copilot | Date: September 2, 2026 | Branch: feature/phase-3-evidence-layer*
