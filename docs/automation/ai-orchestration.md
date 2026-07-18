# AI Orchestration Playbook (Copilot + Cursor + Gemini)

Purpose: define how we execute software delivery with our three paid AI tools, with clear boundaries, handoffs, and quality controls.

## 1) Tool Roles (Single Source of Truth)

### GitHub Copilot (Coding Assistant + PR Quality)
Use Copilot for:
- Inline code completion and quick function scaffolding
- Unit test generation and refactoring suggestions
- PR description drafting and review comment suggestions
- Small/targeted fixes inside existing files

Do **not** use Copilot as the primary tool for broad multi-file architecture changes.

### Cursor (Implementation Driver)
Use Cursor for:
- Multi-file implementation tasks
- Cross-module refactors and codebase-wide edits
- Agentic execution of clearly scoped tasks
- Applying changes that require repository-wide context

Do **not** use Cursor without a clear task definition and acceptance criteria.

### Gemini (Planning/Reasoning and Validation)
Use Gemini for:
- Requirement clarification
- Architecture trade-off analysis
- Test strategy definition
- Risk identification and edge-case discovery
- Drafting acceptance criteria and “definition of done”

Do **not** use Gemini output directly as production code without implementation + review flow.

---

## 2) Standard Delivery Flow (Spec → Build → Verify → Merge)

### Step A — Spec (Gemini-led)
Input:
- Problem statement
- Constraints
- Existing architecture context

Output (required):
- Scope
- Acceptance criteria
- Risks/assumptions
- Test scenarios

Artifact:
- Add/update issue description with the above sections.

### Step B — Build (Cursor-led)
Input:
- Approved issue scope + acceptance criteria
- Target branch
- Non-goals

Output (required):
- Code changes
- Minimal docs updates
- Initial tests

Artifact:
- Feature branch + commits linked to issue.

### Step C — Verify (Copilot-led + human confirmation)
Input:
- Branch diff
- Acceptance criteria

Output (required):
- Suggested test improvements
- PR summary and risk notes
- Review comments on weak spots

Artifact:
- Pull request with completed template and checklist.

### Step D — Merge (Human gate)
Required before merge:
- CI green
- Required approvals
- Acceptance criteria validated
- No secret leakage
- Rollback path noted (if applicable)

---

## 3) Handoff Contract (Mandatory in every issue/PR)

Each task must include:

### Context
What problem is being solved and why now.

### Scope
Exactly what is in/out.

### Acceptance Criteria
Clear pass/fail bullets.

### Constraints
Security, performance, compliance, timeline, compatibility.

### Test Plan
Unit/integration/e2e expectations.

### AI Tool Assignment
- Spec: Gemini
- Build: Cursor
- Verify: Copilot
- Final sign-off: Human reviewer

---

## 4) Quality Gates for AI-assisted code

Minimum gates:
- Lint passes
- Tests pass
- Type checks pass (where applicable)
- No secrets in repo
- PR template completed
- Docs updated when architecture/behavior changes

Recommended extra gates:
- Coverage threshold check
- Dependency vulnerability scan
- Changed-files policy checks (e.g., docs required for architecture edits)

---

## 5) Prompting Rules (Operational)

### Gemini prompt starter
“Given this repository context and objective, produce: scope, acceptance criteria, risks, assumptions, and test scenarios. Keep outputs implementation-ready and concise.”

### Cursor prompt starter
“Implement only the scoped acceptance criteria for this issue. Keep changes minimal, update tests, and avoid unrelated refactors. Summarize changed files and rationale.”

### Copilot review prompt starter
“Review this PR against acceptance criteria. Identify correctness, test gaps, security concerns, and maintainability risks. Provide actionable comments.”

---

## 6) Definition of Done (DoD)

A task is done only when:
1. Acceptance criteria are all met
2. CI is green
3. Reviewer approval obtained
4. Documentation updated as needed
5. Deployment/rollback notes included (for release-impacting changes)

---

## 7) Anti-patterns to avoid

- Tool overlap without ownership
- Large AI-generated PRs with unclear intent
- Missing acceptance criteria
- Skipping human review for sensitive code paths
- Mixing unrelated refactors into feature delivery

---

## 8) Ownership

- Engineering lead/reviewer owns final quality gate.
- AI tools assist; humans remain accountable for shipped outcomes.
