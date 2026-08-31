import re
from pathlib import Path

import yaml
from django.conf import settings

GATEWAY_DEFINITION = Path(settings.BASE_DIR) / "data/apigw-definitions/bk-apigateway-definition.yaml"

EXPECTED_BK_AUTH_INNER_RESOURCES = {
    "v2_inner_list_mcp_server",
    "v2_inner_lookup_mcp_servers",
    "v2_inner_lookup_gateways",
    "v2_inner_list_gateway_released_resources",
    "v2_inner_lookup_gateway_released_resources",
    "v2_inner_list_oauth2_resource_scopes",
    "v2_inner_list_oauth2_mcp_server_scopes",
}


def _load_gateway_definition() -> dict:
    definition_text = GATEWAY_DEFINITION.read_text()
    definition_text = re.sub(
        r"(?m)(:\s*)\{\{[^}]+}}(\s*)$",
        r'\1"template-value"\2',
        definition_text,
    )
    return yaml.safe_load(definition_text)


def test_bk_auth_has_expected_inner_resource_grants():
    definition = _load_gateway_definition()
    bk_auth_grant = next(grant for grant in definition["grant_permissions"] if grant["bk_app_code"] == "bk_auth")

    assert set(bk_auth_grant["resource_names"]) >= EXPECTED_BK_AUTH_INNER_RESOURCES
