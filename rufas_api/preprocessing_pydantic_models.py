from json import load as load_json
from pathlib import Path
from typing import Generator

from yaml import safe_load as load_yaml


def get_schemas(path_dir_schemas: Path) -> Generator[dict, None, None]:
    for p in path_dir_schemas.iterdir():
        with p.open(mode='r') as f:
            if (ext := p.suffix) == '.json':
                yield load_json(f)
            elif ext in ('.yaml', '.yml'):
                yield load_yaml(f)


def main():
    from rufas_api.config import Paths
    from datamodel_code_generator import InputFileType, generate, DataModelType
    paths = (v for v in Paths.GENERATED_FILES.iterdir() if v.suffix in ('.json', 'yaml', 'yml'))
    for pth in paths:
        generate(
            input_=pth,
            input_file_type=InputFileType.JsonSchema if pth.suffix == '.json' else InputFileType.Yaml,
            output=Paths.GENERATED_FILES / f"{pth.stem.replace('schema_', 'model_')}.py",
            output_model_type=DataModelType.PydanticV2BaseModel,
            field_constraints=True,
            no_alias=True,
            use_default_kwarg=True
        )


if __name__ == "__main__":
    main()
