from pathlib import Path


class Paths:
    _ROOT: Path = Path(__file__).parents[1]
    _INPUTS: Path = _ROOT / 'input'
    _METADATA_PROPERTIES: Path = _ROOT / 'input/metadata/properties'
    METADATA: dict[str, Path] = {
        'default_properties': _METADATA_PROPERTIES / 'default.json',
        'tasks_properties': _METADATA_PROPERTIES / 'tasks_properties.json'
    }

    GENERATED_FILES: Path = Path(__file__).parent / 'automatically_generated'
