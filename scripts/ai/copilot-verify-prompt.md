# Copilot Verify Prompt Pack

Use this prompt to review a PR against acceptance criteria before human sign-off.

## Prompt
You are reviewing a pull request in the SRM Core repository.

Review this PR against acceptance criteria. Identify correctness, test gaps, security concerns, and maintainability risks. Provide actionable comments.

Given the PR diff and issue below, produce:
1) Pass/fail assessment against each acceptance criterion
2) Suggested test improvements
3) PR summary and risk notes
4) Review comments on weak spots (correctness, security, maintainability)

Rules:
- Be specific and actionable; cite files/areas when possible.
- Do not approve by default; call out blockers clearly.
- Check for secret leakage and missing docs when behavior changed.
- Confirm Definition of Done gates are addressed.

## Inputs
### Issue / Acceptance Criteria
<PASTE ISSUE HERE>

### PR Diff / Summary
<PASTE PR DIFF OR SUMMARY HERE>
