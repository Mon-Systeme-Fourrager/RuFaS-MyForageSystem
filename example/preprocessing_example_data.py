from json import load, dump
from pathlib import Path
from shutil import copyfile

INPUT_FILES = {
    "input/task_manager_metadata.json": [
        "files.tasks.path",
        "files.properties.path"
    ],
    "input/data/tasks/example_freestall_task.json": [
        "input_data_csv_export_path",
        {"tasks": [
            "metadata_file_path",
            # "output_prefix",
            "logs_directory",
            "properties_file_path",
            "comparison_properties_file_path",
            "save_animals_directory",
            "filters_directory",
            "csv_output_directory",
            "json_output_directory",
            "report_directory",
            "graphics_directory",
        ]}
    ],
    "input/metadata/example_freestall_dairy_metadata.json": [
        "files.config.path",
        "files.animal.path",
        "files.animal_population.path",
        "files.animal_net_merit.path",
        "files.animal_top_listing_semen.path",
        "files.lactation.path",
        "files.economy.path",
        "files.emission.path",
        "files.purchased_feeds_emissions.path",
        "files.purchased_feed_land_use_change_emissions.path",
        "files.feed.path",
        "files.NRC_Comp.path",
        "files.NASEM_Comp.path",
        "files.manure_management.path",
        "files.manure_processor_connection.path",
        "files.crop_configurations.path",

        "files.field_1.path",
        "files.soil_1.path",
        "files.Corn-Alf-Silage.path",
        "files.fertilizer_schedule_1.path",
        "files.manure_schedule_1.path",
        "files.tillage_schedule_1.path",

        "files.field_2.path",
        "files.soil_2.path",
        "files.CornGrain-AlfHay.path",
        "files.fertilizer_schedule_2.path",
        "files.manure_schedule_2.path",
        "files.tillage_schedule_2.path",

        "files.weather.path",
        "files.user_feeds.path",
        "files.tractor_dataset.path",
        "files.EEE_constants.path",
        "files.properties.path",
        "files.feed_management.path",
    ],

    # data
    "input/data/animal/animal_genetics/NetMerit_HO.csv": [],
    "input/data/animal/animal_genetics/TopListingSemen_HO.csv": [],
    "input/data/animal/animal_population.json": [],
    "input/data/animal/example_freestall_animal.json": [],
    "input/data/animal/lactation_curve_adjustment_inputs.json": [],
    "input/data/config/example_freestall_config.json": [],
    "input/data/crop/example_alf_corn_silage_rotation.json": [],
    "input/data/crop/example_alf_hay_corn_grain_rotation.json": [],
    "input/data/crop_configurations/default_crop_configs.json": [],
    "input/data/EEE/constants.json": [],
    "input/data/EEE/default_costs.csv": [],
    "input/data/EEE/default_emissions.csv": [],
    "input/data/EEE/full_feeds_emissions_July2024_interpolated_regional_average.csv": [],
    "input/data/EEE/full_feeds_land_use_change_emissions_July2024_interpolated_regional_average.csv": [],
    "input/data/EEE/tractor_dataset.csv": [],
    "input/data/feed/example_Midwest_feed.json": [],
    "input/data/feed/NASEM_Comp_with_TDN.csv": [],
    "input/data/feed/NRC_comp.csv": [],
    "input/data/feed/user_feeds.csv": [],
    "input/data/feed_management/example_feed_management.json": [],
    "input/data/fertilizer_schedule/example_sm_alf_corn_fertilizer.json": [],
    "input/data/field/example_small_field_corn_alf_silage.json": [],
    "input/data/field/example_small_field_corn_grain_alf_hay.json": [],
    "input/data/manure/example_freestall_processor_configs.json": [],
    "input/data/manure/example_freestall_processor_connections.json": [],
    "input/data/manure_schedule/example_sm_corn_alf_manure_schedule.json": [],
    "input/data/soil/example_soil.json": [],
    "input/data/soil/example_soil_2.json": [],
    # "input/data/tasks/example_freestall_task.json": [],
    "input/data/tillage_schedule/no_till.json": [],
    "input/data/weather/example_temperate_weather.csv": [],

    # metadata
    "input/metadata/properties/default.json": [],
    "input/metadata/properties/tasks_properties.json": [
        "tasks_properties.input_data_csv_export_path.default",
        "tasks_properties.tasks.properties.metadata_file_path.default",
        "tasks_properties.tasks.properties.properties_file_path.default",
        "tasks_properties.tasks.properties.comparison_properties_file_path.default",
    ],
    # "input/metadata/example_freestall_dairy_metadata.json": [],

}


def _change_path(
        p: str,
        path_dir_inputs: Path,
        path_dir_outputs: Path,
) -> Path:
    parts = p.split("/")
    parent = parts[0]
    if parent == 'input':
        parent_path = path_dir_inputs
    elif parent == 'output':
        parent_path = path_dir_outputs
    else:
        raise RuntimeError(f"Unknown parent {parent}")
    return parent_path / '/'.join(parts[1:])


def set_by_dot(d: dict, path_keys: str, value: str):
    keys = path_keys.split(".")
    for k in keys[:-1]:
        d = d[k]
    d[keys[-1]] = value


def copy_input_files(path_dir_inputs: Path) -> None:
    for v in INPUT_FILES.keys():
        path_source = Path(f'../{v}')
        path_target = path_dir_inputs / '/'.join(v.split('/')[1:])
        path_target.parent.mkdir(parents=True, exist_ok=True)
        copyfile(src=str(path_source), dst=str(path_target))


def _handle_single_value(
        data: dict,
        item: str,
        path_dir_inputs: Path,
        path_dir_outputs: Path,
) -> None:
    relative_access_path = "".join([f'["{s}"]' for s in item.split('.')])
    p = _change_path(
        p=eval("data" + relative_access_path),
        path_dir_inputs=path_dir_inputs,
        path_dir_outputs=path_dir_outputs
    )
    set_by_dot(d=data, path_keys=item, value=p.as_posix())


def _handle_tasks(
        access_path: list[str],
        data: dict,
        path_dir_inputs: Path,
        path_dir_outputs: Path,
) -> None:
    for item in access_path:
        if isinstance(item, str):
            _handle_single_value(
                data=data,
                item=item,
                path_dir_inputs=path_dir_inputs,
                path_dir_outputs=path_dir_outputs,
            )
        elif isinstance(item, dict):
            for k, values in item.items():
                for v_data in data[k]:
                    for v in values:
                        _handle_single_value(
                            data=v_data,
                            item=v,
                            path_dir_inputs=path_dir_inputs,
                            path_dir_outputs=path_dir_outputs,
                        )

        pass


def change_paths(
        path_dir_inputs: Path,
        path_dir_outputs: Path,
) -> None:
    to_modify: dict = {k: v for k, v in INPUT_FILES.items() if len(v) > 0}
    for k, v in to_modify.items():
        path_target = path_dir_inputs / '/'.join(k.split('/')[1:])
        with path_target.open('r', encoding='utf-8') as f:
            data = load(f)
        if not path_target.parent.stem == 'tasks':
            for item in v:
                _handle_single_value(
                    data=data,
                    item=item,
                    path_dir_inputs=path_dir_inputs,
                    path_dir_outputs=path_dir_outputs,
                )
        else:
            _handle_tasks(
                access_path=v,
                data=data,
                path_dir_inputs=path_dir_inputs,
                path_dir_outputs=path_dir_outputs,
            )
        with path_target.open('w', encoding='utf-8') as f:
            dump(data, f, indent=3)

    pass


def create_output_files(
        path_dir_outputs: Path
) -> None:
    path_filters: Path = path_dir_outputs / 'output_filters/csv_feed_manager.txt'
    path_filters.parent.mkdir(parents=True, exist_ok=True)
    with path_filters.open('w', encoding='utf-8') as f:
        f.write('FeedManager.*')


def create_example_files(
        path_dir_inputs: Path,
        path_dir_outputs: Path,
        is_create_output_files: bool = False,
) -> None:
    if is_create_output_files:
        create_output_files(path_dir_outputs=path_dir_outputs)

    copy_input_files(path_dir_inputs=path_dir_inputs)

    change_paths(
        path_dir_inputs=path_dir_inputs,
        path_dir_outputs=path_dir_outputs,
    )


if __name__ == "__main__":
    path_root = Path(__file__).parent
    create_example_files(
        path_dir_inputs=path_root / "inputs_example",
        path_dir_outputs=path_root / "outputs_example",
        is_create_output_files=True
    )
