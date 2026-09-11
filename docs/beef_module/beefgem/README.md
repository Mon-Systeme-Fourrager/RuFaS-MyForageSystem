# docs/beef_module/beefgem/

BeefGEM management enhancement layer — reference documents.

## Files

### `RuFaS_BeefGEM_Implementation_Plan.md` — implement from this

The execution plan for the `feature/beef-beefgem-management` PR.
Written in RuFaS style (plain Enum, mypy strict, scoped Black, TDD).
Covers Phases A–D in strict dependency order.

### `RuFaS_BeefGEM_Management_Implementation_Plan.docx` — source reference only

The June 2026 source document (BeefGEM 4.0 / USDA-ARS Rotz et al.).
Contains BeefGEM rule IDs (R-CH4-ENT-003, D-STOCKER-TO-FINISH-001, …),
`simulate.py` / `herd_dynamics.py` / `physiology.py` source mappings,
the `COW_CALF_STOCKER_FEEDLOT` grouping scenario definition, test-marker
taxonomy, and five named future-PR gaps (Section 10).

**Phase B (Steps B-1 and B-2) in the DOCX is superseded.** The native
stocker module it describes was delivered by PR #47 and merged to dev-msf.
Implement from the `.md` plan, not from the DOCX.

Code blocks in the DOCX were flattened by the pandoc conversion and
re-fenced heuristically — treat them as indicative, not copy-paste ready.

## OpenSpec

The four OpenSpec artifacts at `openspec/changes/beef-beefgem-management/`
(`proposal.md`, `design.md`, `specs.md`, `tasks.md`) were derived from the
`.md` execution plan and are the authoritative task checklist for
`/apply-plan`.
