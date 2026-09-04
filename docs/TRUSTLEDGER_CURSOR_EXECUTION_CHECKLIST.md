# Cursor Execution Checklist — First Actual Code Batch

> Use this checklist for the first implementation batch after the scoping and sequence documents are approved.
>
> This checklist assumes the repo now has:
> - `docs/TRUSTLEDGER_IMPLEMENTATION_CHARTER.md`
> - `docs/TRUSTLEDGER_CONSOLIDATED_IMPLEMENTATION_SEQUENCE.md`
> - `docs/TRUSTLEDGER_MODULE_IMPLEMENTATION_MATRIX.md`

---

## 1. Batch identity

**Batch name:** Enhance existing modules safely

**Batch objective:** Make the first additive, backward-compatible code changes to existing SRM modules so they become trust-aware without changing current user workflows.

**Do not proceed until:**
- the batch scope is approved,
- the current repo state is understood,
- and the implementation lead has confirmed the target files.

---

## 2. Pre-flight checks

Before editing anything, confirm:
- [ ] The governing docs are present and readable
- [ ] The target module areas are identified
- [ ] The current behavior is understood
- [ ] The batch scope is narrow and additive
- [ ] No destructive refactor is required
- [ ] No current workflow depends on the fields or behavior being changed
- [ ] A rollback path exists if needed

If any item is unclear, stop and ask for guidance before editing.

---

## 3. Target areas for this batch

Focus only on the current module layer:

- [ ] Measurement / outcome
- [ ] Stakeholder response
- [ ] Evidence
- [ ] Segmentation / geography
- [ ] AI helper methods

Do not expand outside this list unless explicitly approved.

---

## 4. Required implementation approach

For each target area:
- [ ] Preserve existing behavior
- [ ] Add optional trust-aware support only
- [ ] Keep changes localized
- [ ] Avoid renaming existing fields or modules
- [ ] Avoid breaking API contracts
- [ ] Add helper methods or optional extensions where possible
- [ ] Keep logic explainable and deterministic
- [ ] Add tests for behavior changes

---

## 5. Suggested implementation order

### Step 1 — Measurement / outcome
- [ ] Add optional trust-oriented fields or helper logic
- [ ] Keep existing outcome calculations intact
- [ ] Confirm current reports still work

### Step 2 — Stakeholder response
- [ ] Extend response capture for trust, willingness, or confidence
- [ ] Preserve current response semantics
- [ ] Confirm current capture flows still work

### Step 3 — Evidence
- [ ] Add trust tagging or trust linkage support
- [ ] Preserve current verification behavior
- [ ] Confirm evidence workflows still work

### Step 4 — Segmentation / geography
- [ ] Add trust-friendly grouping helpers
- [ ] Preserve existing segmentation meanings
- [ ] Confirm no downstream breakage

### Step 5 — AI helper methods
- [ ] Add trust-aware hooks or prompt helpers
- [ ] Keep AI outputs advisory only
- [ ] Preserve current deterministic behavior

---

## 6. Change discipline

During implementation:
- [ ] Make the smallest safe change set
- [ ] Prefer optional fields over mandatory ones
- [ ] Prefer adapters/helpers over rewrites
- [ ] Avoid unrelated cleanup
- [ ] Avoid large formatting-only diffs unless necessary
- [ ] Keep commit scope focused on the batch objective

---

## 7. Testing checklist

Before finishing the batch:
- [ ] Add tests for any new trust-aware behavior
- [ ] Confirm existing tests still pass for untouched behavior
- [ ] Validate compatibility with current modules
- [ ] Verify that no workflow was unintentionally changed
- [ ] Check for regressions in reports, evidence, or response capture

---

## 8. Documentation checklist

If the batch changes behavior or introduces a new safe reference point:
- [ ] Update relevant docs
- [ ] Note the new trust-aware behavior
- [ ] Explain what remains unchanged
- [ ] Keep documentation consistent with the charter and matrix

---

## 9. Review and handoff

When complete, report:
- [ ] Files changed
- [ ] What was added
- [ ] What stayed untouched
- [ ] Compatibility notes
- [ ] Tests added or updated
- [ ] Any remaining risks
- [ ] Recommendation for the next batch

---

## 10. Stop condition

After completing the first actual code batch:
- [ ] Stop
- [ ] Do not expand into trust-native structures yet
- [ ] Wait for approval before starting the next batch
