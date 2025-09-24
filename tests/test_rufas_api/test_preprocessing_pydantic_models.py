from json import dumps
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from rufas_api.preprocessing_pydantic_models import get_schemas


def _set_file(
        file_content: dict | str,
        file_extension: str,
) -> Mock:
    func = dumps if file_extension == '.json' else str
    res_file = Mock(spec=Path)
    res_file.suffix = file_extension
    res_file.open = mock_open(read_data=func(file_content))

    return res_file


def test_get_schemas_mixed_files():
    json_file = _set_file(file_content={"type": "object", "properties": {"id": {"type": "integer"}}},
                          file_extension=".json")
    yaml_files = [_set_file(file_content={"type": f"string"}, file_extension=s) for s in ('.yaml', '.yml')]
    other_files = [_set_file(file_content='random_content', file_extension=s) for s in ('.txt', '.csv', 'doc')]

    with patch.object(Path, "iterdir", return_value=(files := [json_file, *yaml_files, *other_files])):
        results = list(get_schemas(Path("dummy")))

    assert len(results) == len(files) - len(other_files)
