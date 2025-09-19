if __name__ == "__main__":
    from rufas_api.config import Paths
    from datamodel_code_generator import InputFileType, generate, DataModelType

    generate(
        input_=Paths.generated_default_properties_specs,
        input_file_type=InputFileType.OpenAPI,
        output=Paths.generated_pydantic_models,
        output_model_type=DataModelType.PydanticV2BaseModel,
        field_constraints=True,
        no_alias=True,
        use_default_kwarg=True
    )
