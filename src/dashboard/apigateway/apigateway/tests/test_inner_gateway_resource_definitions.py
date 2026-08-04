from pathlib import Path

import yaml
from django.conf import settings

RESOURCE_DEFINITIONS = Path(settings.BASE_DIR) / "data/apigw-definitions/bk-apigateway-resources.yaml"
GATEWAY_DEFINITION = Path(settings.BASE_DIR) / "data/apigw-definitions/bk-apigateway-definition.yaml"


EXPECTED_RESOURCES = {
    "/api/v2/inner/gateways/-/lookup/": {
        "operation_id": "v2_inner_lookup_gateways",
        "backend_path": "/backend/api/v2/inner/gateways/-/lookup/",
    },
    "/api/v2/inner/gateways/{gateway_name}/released-resources/": {
        "operation_id": "v2_inner_list_gateway_released_resources",
        "backend_path": "/backend/api/v2/inner/gateways/{gateway_name}/released-resources/",
    },
}


def test_inner_gateway_lookup_resource_definitions():
    resources = yaml.safe_load(RESOURCE_DEFINITIONS.read_text())["paths"]

    for path, expected in EXPECTED_RESOURCES.items():
        operation = resources[path]["get"]
        resource = operation["x-bk-apigateway-resource"]

        assert operation["operationId"] == expected["operation_id"]
        assert resource["backend"]["path"] == expected["backend_path"]
        assert resource["isPublic"] is False
        assert resource["allowApplyPermission"] is False
        assert resource["authConfig"] == {
            "userVerifiedRequired": False,
            "appVerifiedRequired": True,
            "resourcePermissionRequired": True,
        }


def test_bk_auth_has_inner_gateway_lookup_permissions():
    definition_text = GATEWAY_DEFINITION.read_text()
    bk_auth_scope = definition_text.split("  - bk_app_code: bk_auth", maxsplit=1)[1].split(
        "  - bk_app_code:",
        maxsplit=1,
    )[0]

    for expected in EXPECTED_RESOURCES.values():
        assert f"      - {expected['operation_id']}" in bk_auth_scope
