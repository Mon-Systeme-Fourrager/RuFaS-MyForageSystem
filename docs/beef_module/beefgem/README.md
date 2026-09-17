# docs/beef_module/beefgem/

BeefGEM management enhancement layer — reference documents.

## Files

### `RuFaS_BeefGEM_Implementation_Plan.md` — implement from this

The execution plan for the `feature/beef-beefgem-management` PR.
Written in RuFaS style (plain Enum, mypy strict, scoped Black, TDD).
Covers Phases A–D in strict dependency order.

### `RuFaS_BeefGEM_Source_Reference.md` — source provenance, read this one

The readable conversion of the June 2026 source document (BeefGEM 4.0 /
USDA-ARS Rotz et al.). Greppable, diffable, and renders on GitHub, so it is
the primary reference for anything in the source material.

Contains BeefGEM rule IDs (R-CH4-ENT-003, D-STOCKER-TO-FINISH-001, …),
`simulate.py` / `herd_dynamics.py` / `physiology.py` source mappings,
the `COW_CALF_STOCKER_FEEDLOT` grouping scenario definition, test-marker
taxonomy, and five named future-PR gaps (Section 10).

**Its stocker section is superseded.** The native stocker module it
describes is already implemented in the animal subsystem. Implement from
the execution plan above, not from this file.

Code blocks were flattened by the pandoc conversion and re-fenced
heuristically — treat them as indicative, not copy-paste ready.

### `RuFaS_BeefGEM_Management_Implementation_Plan.docx` — archival original

The original Word document the Markdown above was converted from. Kept for
provenance. Prefer the Markdown for reading, searching, and review; consult
the DOCX only to check the conversion or recover formatting it dropped.

Tracked via a scoped exception in `.gitignore` — the repo-wide `*.docx`
rule would otherwise exclude it.

## Coefficient provenance

**Two BeefGEM coefficient sets could not be traced to NRC 2016.**

Grass-fed (`BEEF_CH4_GRASS_FED_*`, 8.25 / 31.2): give 257.85 g/d at
8 kg DM/d, above the 87-252 g/d NRC Ch.16 reports for grazing cattle.
Pinned in the suite as a tripwire.

Stocker forage (`BEEF_CH4_STOCKER_FORAGE_*`, 10.04 / 23.7): the source
document labels these "NASEM 2016, eq 6.8". NRC Ch.6 is protein and
amino acids; enteric methane is Ch.16, Eq. 16-8 and 16-9. Neither
coefficient appears anywhere in the BeefGEM source document, whose own
backgrounding rule R-CH4-ENT-003 uses the four-input Eq. 16-8 form
(71.5 + 0.12*BW + 0.10*DMI^3 - 244.8*fat). Output values do fall
inside the NRC range across the working intake band, but the equation
itself has no identified source.

Both are implemented as pinned, for traceability. Neither should be
treated as NRC-sourced without re-derivation.

## OpenSpec

The four OpenSpec artifacts at `openspec/changes/beef-beefgem-management/`
(`proposal.md`, `design.md`, `specs.md`, `tasks.md`) were derived from the
`.md` execution plan and are the authoritative task checklist for
`/apply-plan`.
