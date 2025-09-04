from pathlib import Path

from RUFAS import task_manager
from preprocessing_example_data import create_example_files
from rufas_api.launching import launch_rufas


def redirect_pyproject_path() -> None:
    task_manager.PYPROJECT_FILE_PATH = "../pyproject.toml"


if __name__ == '__main__':
    path_root: Path = Path(__file__).parent
    path_dir_inputs: Path = path_root / "inputs_example"
    path_dir_outputs: Path = path_root / 'outputs_example'
    redirect_pyproject_path()
    create_example_files(
        path_dir_inputs=path_root / "inputs_example",
        path_dir_outputs=path_dir_outputs,
        is_create_output_files=True
    )

    launch_rufas(
        path_to_metadata=path_dir_inputs / 'task_manager_metadata.json',
        verbose='credits',
        exclude_info_maps=False,
        output_dir=path_dir_outputs,
        logs_dir=path_dir_outputs / 'logs',
        clear_output=False,
        no_graphics=False,
        suppress_log_files=False,
        metadata_depth_limit=None,
    )
