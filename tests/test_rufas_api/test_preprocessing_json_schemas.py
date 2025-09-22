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


class TestVerifyJsonSchemaStructure:

    def test_empty_dict(self):
        assert verify_json_schema_structure(d={})

    def test_dict_without_type(self):
        assert verify_json_schema_structure(d={"title": "Test", "description": "A test schema"})

    def test_object_type_with_properties(self):
        schema = {
            "type": "object",
            "properties": {
                "start_date": {
                    "type": "string",
                    "description": "The year and Julian day on which the simulation will start.",
                    "default": "2009:1"
                },
                "end_date": {
                    "type": "string",
                    "description": "The year and Julian day on which the simulation will end.",
                    "default": "2009:100"
                }
            }
        }
        assert verify_json_schema_structure(d=schema)

    def test_object_type_without_properties(self):
        schema = {
            "type": "object",
            "title": "Test Object"
        }
        assert not verify_json_schema_structure(d=schema)

    def test_array_type_with_items(self):
        schema = {
            "type": "array",
            "items": {"type": "string"}
        }
        assert verify_json_schema_structure(d=schema)

    def test_array_type_without_items(self):
        schema = {
            "type": "array",
            "title": "Test Array"
        }
        assert not verify_json_schema_structure(d=schema)

    def test_primitive_types(self):
        assert verify_json_schema_structure(d={"type": "string"})

        schema = {"type": "number"}
        result = verify_json_schema_structure(schema)
        assert result

    def test_nested_object_structure(self):
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "number"}
                    }
                }
            }
        }
        assert verify_json_schema_structure(d=schema)

    def test_nested_array_structure(self):
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"}
                }
            }
        }
        assert verify_json_schema_structure(schema)

    def test_mixed_valid_invalid_structure(self):
        schema = {
            "type": "object",
            "properties": {
                "valid_nested": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "invalid_nested": {
                    "type": "object"
                    # Missing properties field
                }
            }
        }
        assert not verify_json_schema_structure(d=schema)

    def test_deep_nesting(self):
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "level3": {"type": "string"}
                                }
                            }
                        }
                    }
                }
            }
        }
        assert verify_json_schema_structure(d=schema)

    def test_non_dict_values_ignored(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "tags": ["tag1", "tag2"],  # This list should be ignored
                "count": 42  # This number should be ignored
            }
        }
        assert verify_json_schema_structure(d=schema)


def test_read_metadata_returns_dict():
    metadata = preprocessing_json_schemas.read_metadata(path_metadata=PATH_METADATA / 'default.json')
    assert isinstance(metadata, dict)


def test_create_schema_properties_returns_valid_json_schema():
    api_specs = preprocessing_json_schemas.create_schema_properties(
        meta=preprocessing_json_schemas.read_metadata(path_metadata=PATH_METADATA / 'default.json'))
    Draft202012Validator.check_schema(schema=api_specs)
    assert verify_json_schema_structure(d=api_specs), 'The JSON schema structure was not valid'
