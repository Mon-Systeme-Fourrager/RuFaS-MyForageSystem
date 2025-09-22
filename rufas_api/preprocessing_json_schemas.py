"""Create JSON Schemas compliant with OpenAPI 3.1 sepcs
"""

from copy import deepcopy
from dataclasses import dataclass
from json import loads, dumps as dump_json
from pathlib import Path
from typing import Any

from yaml import dump as dump_yaml


def read_metadata(path_metadata: Path) -> dict:
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


def _get_required_properties(d: dict) -> list[str]:
    return [k for k, v in d.items() if 'default' not in v]


def extract_properties(d: dict) -> dict:
    _d = deepcopy(d)
    _type = get_python_type(field_type=_d.pop("type")).name
    prop = {"type": _type, **({"format": "float"} if _type is float else {}),
            "description": _d.pop("description") if "description" in _d else ""}
    if "default" in _d:
        _default = _d.pop("default")
        prop["default"] = _default if _default is None else float(_default) if _type == "number" else int(
            _default) if _type == "integer" else _default

    for k in list(_d):
        if not isinstance(_d[k], dict):
            prop[k] = _d.pop(k)

    properties = {}
    for k, v in _d.items():
        properties[k] = extract_properties(d=v)

    if len(properties) > 0:
        if len(properties) == 1:
            if _type == "array":
                prop['items'] = properties['properties']
            elif _type == "object":
                prop['properties'] = properties
        else:
            prop["properties"] = properties

        if _type == 'object':
            if len(required_properties := _get_required_properties(d=properties)) > 0:
                prop['required'] = required_properties

    return prop


def create_schema_properties(meta: dict) -> dict[str, ...]:
    res = {}
    for k, v in meta.items():
        if isinstance(v, dict):
            if "type" in v:
                res[k] = extract_properties(d=v)
            else:
                res[k] = {
                    "type": "object",
                    "properties": create_schema_properties(meta=v)
                }
                if len(required_properties := _get_required_properties(d=res[k]['properties'])) > 0:
                    res[k]["required"] = required_properties

        else:
            if not k == 'data_collection_app_compatible':
                res[k] = v
    return res


def create_schemas(meta: dict[str, Any]) -> dict[str, Any]:
    res: dict[str, Any] = {
        "type": "object",
        "description": meta.get("description", ""),
        "properties": create_schema_properties(meta=meta)
    }

    if len(required_properties := _get_required_properties(d=res['properties'])) > 0:
        res["required"] = required_properties

    return res


def write_schemas(
        schemas: dict[str, dict[str, Any]],
        path_dir: Path,
        is_yaml: bool = False,
) -> None:
    func, kwargs = (dump_yaml, {}) if is_yaml else (dump_json, {"indent": 4})
    for k, v in schemas.items():
        (path_dir / f"schema_{k}.json").write_text(func(v, sort_keys=False, **kwargs))


if __name__ == "__main__":
    from rufas_api.config import Paths

    Paths.GENERATED_FILES.mkdir(parents=True, exist_ok=True)

    write_schemas(
        schemas={k: create_schemas(meta=read_metadata(path_metadata=v)) for k, v in Paths.METADATA.items()},
        path_dir=Paths.GENERATED_FILES,
    )
