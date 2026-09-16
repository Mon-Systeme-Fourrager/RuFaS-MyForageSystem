"""
adapters — RUFAS ↔ Spatializer Evaluators bridge

Converts RUFAS simulation state into the *Inputs dataclasses
that Spatializer evaluators consume. Each evaluator has its
own adapter:

- rufas_to_runoff.py     → RunoffInputs
- rufas_to_compaction.py → SoilInputs + TractorInputs (TODO)
- rufas_to_weather.py    → WeatherInputs (TODO)

Design principles:
- One module per evaluator (independent evolution)
- Adapter receives SimulationEngine (or FieldManager) + field name
- Missing data raises IncompleteRufasStateError
- Adapter never modifies RUFAS state (read-only)
"""
