from apigateway.apps.openapi.models import OpenAPIResourceSchemaVersion


def get_resource_id_to_schema_by_resource_version(resource_version_id: int) -> dict:
    resources_version_schema = OpenAPIResourceSchemaVersion.objects.filter(
        resource_version_id=resource_version_id
    ).first()
    if resources_version_schema is None:
        return {}

    return {schema_info["resource_id"]: schema_info["schema"] for schema_info in resources_version_schema.schema}
