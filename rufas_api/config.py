from pathlib import Path


class Paths:
    _root: Path = Path(__file__).parents[1]
    metadata_properties: Path = _root / 'input/metadata/properties'
    metadata_default_properties: Path = metadata_properties / 'default.json'

    generated_files: Path = Path(__file__).parent / 'automatically_generated'
