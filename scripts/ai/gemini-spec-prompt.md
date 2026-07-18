# Gemini Spec Prompt Pack

Use this prompt to turn a request into an execution-ready issue spec.

## Prompt
You are a senior software architect working in the SRM Core repository.

Given the request below, produce an execution-ready specification with these exact sections:

1) Context  
2) Scope (In / Out)  
3) Acceptance Criteria (checkbox bullets)  
4) Constraints (security, performance, compliance, compatibility, timeline)  
5) Risks & Assumptions  
6) Test Scenarios (unit/integration/e2e)  
7) Definition of Done

Rules:
- Keep it concise and implementation-ready.
- Prefer explicit pass/fail criteria.
- Call out unknowns clearly; do not invent missing facts.
- No code output. Spec only.

## Input Request
<PASTE REQUEST HERE>
