# AI Task Lifecycle (Gemini → Cursor → Copilot)

This runbook defines the mandatory lifecycle for delivering work in SRM Core using AI tools.

## 1) Intake
Create a new GitHub issue using **AI Task** template.

Required fields:
- Context
- Scope (In/Out)
- Acceptance Criteria
- Constraints
- Test Plan
- Tool assignment (Gemini/Cursor/Copilot)

## 2) Spec (Gemini)
Use `scripts/ai/gemini-spec-prompt.md`.

Output must be added to the issue:
- Refined scope
- Explicit acceptance criteria
- Risks/assumptions
- Test scenarios
- Definition of done

## 3) Build (Cursor)
Use `scripts/ai/cursor-implementation-prompt.md`.

Execution rules:
- Implement only approved scope
- Keep diffs minimal
- Add/update tests
- Avoid unrelated refactors

## 4) Verify (Copilot + Human)
Use `scripts/ai/copilot-verify-prompt.md`.

Verification output required in PR:
- Pass/needs-changes verdict
- Blocking/non-blocking findings
- Missing tests
- Merge readiness checklist

## 5) Merge Gates (Mandatory)
PR can merge only if:
- CI checks pass
- Acceptance criteria satisfied
- Reviewer approval obtained
- Docs updated when behavior/architecture changed
- No secrets or policy violations

## 6) Post-merge
- Confirm branch cleanup
- Confirm deployment path (if applicable)
- Capture any follow-up tasks as new AI Task issues

## 7) Traceability
Every PR should reference:
- Source AI Task issue
- Which prompt packs were used
- Human validation performed

Recommended PR note format:

- Spec: Gemini (`scripts/ai/gemini-spec-prompt.md`)
- Build: Cursor (`scripts/ai/cursor-implementation-prompt.md`)
- Verify: Copilot (`scripts/ai/copilot-verify-prompt.md`)
- Human checks: <what was manually verified>
