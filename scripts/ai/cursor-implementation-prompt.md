# Cursor Implementation Prompt Pack

Use this prompt when implementing an approved AI Task issue.

## Prompt
Implement ONLY the approved scope and acceptance criteria for this issue in SRM Core.

Requirements:
- Keep changes minimal and targeted.
- Do not perform unrelated refactors.
- Respect repository guardrails in docs/automation/ai-orchestration.md.
- Add/update tests required by the issue test plan.
- Do not commit secrets or credentials.

Output format required:
1) Summary of changes
2) Files changed (with purpose per file)
3) Tests added/updated
4) Any assumptions made
5) Suggested commit message (Conventional Commits)

Issue spec:
<PASTE ISSUE CONTENT HERE>
