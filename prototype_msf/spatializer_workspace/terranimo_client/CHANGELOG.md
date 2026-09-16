# Changelog

All notable changes to `terranimo_client` are documented here.

## [0.3.0] — 2026-09-15

### BREAKING CHANGES
- Renamed `matric_potential_cbar` → `matric_potential_bar` 
  in 3 client functions (VG water content, precompression, 
  tyre_for_compaction). Values were already in bar internally; 
  only the parameter name was misleading.
- README examples corrected: `matric_potential_cbar=33` → 
  `matric_potential_bar=0.33`

### Migration guide

Callers who previously passed cbar values (e.g., 
`matric_potential_cbar=33` for field capacity) must divide 
by 100 when using the new parameter 
(`matric_potential_bar=0.33`). The API always interpreted 
values in bar; the old parameter name was misleading, not 
the values themselves.

### Added
- "Unit conventions" section in README documenting units 
  per parameter, based on Stefan Gfeller confirmation 
  (2026-09-15).

### Fixed
- Compaction Evaluator (spatializer_v2/evaluators/compaction.py) 
  updated to use new kwarg name.
