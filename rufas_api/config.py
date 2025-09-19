from pathlib import Path


class Paths:
    _root: Path = Path(__file__).parents[1]
    metadata_properties: Path = _root / 'input/metadata/properties'
    metadata: dict[str, Path] = {
        'default_properties': metadata_properties / 'default.json',
        'tasks_properties': metadata_properties / 'tasks_properties.json',
    }

    generated_files: Path = Path(__file__).parent / 'automatically_generated'
