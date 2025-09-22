from pathlib import Path

from jsonschema import Draft202012Validator

from rufas_api import preprocessing_json_schemas

PATH_METADATA = Path(__file__).parent / "sources/metadata"


def verify_json_schema_structure(d: dict) -> bool:
    res = []
    if "type" in d:
        _type = d["type"]
        _name = 'properties' if _type == "object" else "items" if _type == "array" else None
        if _name is not None:
            res.append(_name in d)
    for k, v in d.items():
        if isinstance(v, dict):
            res += [verify_json_schema_structure(d=v)]

    return all(res)

    return res


def test_read_metadata_returns_dict():
    metadata = preprocessing_json_schemas.read_metadata(path_metadata=PATH_METADATA / 'default.json')
    assert isinstance(metadata, dict)


def test_create_schema_properties_returns_valid_json_schema():
    api_specs = preprocessing_json_schemas.create_schema_properties(
        meta=preprocessing_json_schemas.read_metadata(path_metadata=PATH_METADATA / 'default.json'))
    Draft202012Validator.check_schema(schema=api_specs)
    assert verify_json_schema_structure(d=api_specs), 'The JSON schema structure was not valid'
