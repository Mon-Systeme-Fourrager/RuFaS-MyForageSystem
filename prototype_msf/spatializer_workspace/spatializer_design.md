## Integration path — v0.1 → v1.0

### v0.1 (current — implemented)
- Standalone module
- Called with dict input, returns dict output
- No RUFAS integration yet
- Zero external dependencies

### v1.0 (target)
- Called BEFORE FieldManager.__init__ in RUFAS pipeline
- Replaces the single-field dict with N-zone dict
- Requires zero changes inside RUFAS core (validated in Aug 22 sprint)
- Integration point: `run_multiyr_sweep.py` or equivalent orchestrator

### Conceptual flow (before vs after)

**Before Spatializer (current RUFAS):**
```python
field_data = {
    "field_A": {clay: 25, silt: 40, ...}  # 1 entry
}
FieldManager(field_data)  # simulates 1 field
```

**After Spatializer:**
```python
raw_field = {"field_id": "field_A", "mean_slope_pct": 5.0, ...}
zones = spatialize_field(raw_field)  # returns N zones
field_data = {
    "field_A_zone_medium": zones["zone_medium"],
    # more zones if applicable
}
FieldManager(field_data)  # simulates N zones per field
```

### Open architectural questions

- **Orchestration mechanism:** Python script vs Django API vs AWS 
  Step Functions? — pending Rami input
- **Data flow:** file-based vs DB-based vs in-memory? — pending 
  Rami input
- **Caching strategy:** recompute per request vs precompute + cache? 
  — pending scale definition from Maxime
- **Concurrency:** how many fields simulated in parallel? — depends 
  on infrastructure decision above
