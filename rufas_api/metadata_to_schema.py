from copy import deepcopy
from dataclasses import dataclass
from json import loads, dump
from pathlib import Path

from rufas_api.config import Paths


def read_meta_data(path_metadata: Path) -> dict:
    return loads(path_metadata.read_text())


@dataclass
class _Var:
    type: type
    name: str


def get_python_type(field_type: str) -> _Var:
    """Map string types to Python types."""
    match field_type:
        case "string" | "str":
            res = _Var(type=str, name="string")
        case "float" | "number":
            res = _Var(type=float, name="number")
        case "integer" | "int":
            res = _Var(type=int, name="integer")
        case "boolean" | "bool":
            res = _Var(type=bool, name="boolean")
        case "array" | "list" | "tuple":
            res = _Var(type=list, name="array")
        case "object" | "dict":
            res = _Var(type=dict, name="object")
        case _:
            raise Exception(f"Unknown field type: {field_type}")
    return res


def extract_properties(d: dict) -> dict:
    _d = deepcopy(d)
    _type = get_python_type(field_type=_d.pop("type")).name
    prop = {"type": _type, **({"format": "float"} if _type is float else {}),
            "description": _d.pop("description") if "description" in _d else ""}
    if "default" in _d:
        _default = _d.pop("default")
        prop["default"] = _default if _default is None else float(_default) if _type == "number" else int(
            _default) if _type == "integer" else _default
    prop.update(**_d)
    return prop


def create_schema_properties(meta: dict) -> dict[str, ...]:
    res = {}
    for k, v in meta.items():
        if isinstance(v, dict):
            if "type" in v:
                res[k] = extract_properties(d=v)
                for k2, v2 in v.items():
                    if isinstance(v2, dict):
                        res[k][k2] = extract_properties(d=v2)
            else:
                res[k] = {
                    "type": "object",
                    "properties": create_schema_properties(meta=v)
                }
        else:
            if not k == 'data_collection_app_compatible':
                res[k] = v
    return res


if __name__ == "__main__":
    meta_data = read_meta_data(path_metadata=Paths.metadata_default_properties)
    didi = create_schema_properties(meta=meta_data)

    with (Path(__file__).parent / 'schema_props.json').open(mode='w') as f:
        dump(didi, f)
