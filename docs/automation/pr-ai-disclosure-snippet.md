# PR AI Disclosure Snippet

Copy/paste this into pull requests.

## AI Assistance Disclosure

- **Spec tool:** Gemini  
  - Prompt pack: `scripts/ai/gemini-spec-prompt.md`
  - What it produced: scope, acceptance criteria, risks, test scenarios

- **Build tool:** Cursor  
  - Prompt pack: `scripts/ai/cursor-implementation-prompt.md`
  - What it produced: implementation across scoped files + tests

- **Verify tool:** GitHub Copilot  
  - Prompt pack: `scripts/ai/copilot-verify-prompt.md`
  - What it produced: PR review findings, gaps, merge-readiness checks

## Human Validation Performed

- [ ] Acceptance criteria manually checked
- [ ] Sensitive flows manually reviewed (auth/permissions/billing as applicable)
- [ ] Test results reviewed
- [ ] Diff reviewed for unrelated/refactor creep
- [ ] No secrets/credentials in changes

## Traceability

- Issue: `<link to AI Task issue>`
- Prompt packs used:
  - `scripts/ai/gemini-spec-prompt.md`
  - `scripts/ai/cursor-implementation-prompt.md`
  - `scripts/ai/copilot-verify-prompt.md`
