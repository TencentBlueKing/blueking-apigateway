import copy
import json
from types import SimpleNamespace

from apigateway.service.resource_version.openapi_export import OpenAPIExportManager


def test_get_resource_version_openapi_returns_structured_document_without_mutating_snapshot(mocker):
    resource = {
        "id": 1,
        "name": "get_users",
        "description": "Get users",
        "path": "/users/",
        "method": "GET",
        "is_public": True,
        "allow_apply_permission": True,
        "contexts": {"resource_auth": {"config": "{}"}},
        "proxy": {"backend_id": 2, "config": json.dumps({"method": "GET", "path": "/users/"})},
        "plugins": [],
    }
    original = copy.deepcopy(resource)
    resource_version = SimpleNamespace(
        id=3,
        version="1.2.3",
        gateway=SimpleNamespace(id=4, name="demo"),
        data=[resource],
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_backend_id_to_instance",
        return_value={2: SimpleNamespace(name="backend")},
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_gateway_resource_id_to_labels",
        return_value={1: [{"name": "users"}]},
    )
    mocker.patch(
        "apigateway.service.resource_version.openapi_export.get_resource_id_to_schema_by_resource_version",
        return_value={1: {"version": "3.0.1", "responses": {"200": {"description": "OK"}}}},
    )

    document = OpenAPIExportManager(include_bk_apigateway_resource=False).get_resource_version_openapi(
        resource_version
    )

    assert isinstance(document, dict)
    assert document["openapi"] == "3.0.1"
    assert document["paths"]["/users/"]["get"]["tags"] == ["users"]
    assert "x-bk-apigateway-resource" not in document["paths"]["/users/"]["get"]
    assert resource == original
