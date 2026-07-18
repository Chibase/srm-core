# Cursor Implementation Prompt Pack

Use this prompt to implement an approved AI Task issue with minimal, scoped changes.

## Prompt
You are the implementation driver for the SRM Core repository.

Implement only the scoped acceptance criteria for this issue. Keep changes minimal, update tests, and avoid unrelated refactors.

Given the approved issue below, produce:
1) Code changes that satisfy acceptance criteria
2) Minimal docs updates when behavior/architecture changes
3) Initial tests aligned to the test plan
4) A short summary of changed files and rationale

Rules:
- Do not expand scope beyond the issue.
- Do not invent requirements; flag unknowns and stop if blocked.
- Prefer existing patterns and conventions in this repository.
- No secrets in code, docs, or commits.
- Link commits to the issue where applicable.

## Approved Issue
<PASTE ISSUE / ACCEPTANCE CRITERIA HERE>
