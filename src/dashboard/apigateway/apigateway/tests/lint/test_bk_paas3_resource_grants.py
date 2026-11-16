from pathlib import Path

import pytest
from apigw_manager.apigw.management.commands.grant_apigw_permissions import Command
from django.conf import settings

pytestmark = pytest.mark.no_meta_schema


@pytest.mark.parametrize(
    "resource_name",
    [
        "v2_inner_cancel_resource_permission_apply_record",
        "v2_inner_delete_resource_permission_apply_record",
        "v2_inner_cancel_mcp_server_permission_apply_record",
        "v2_inner_delete_mcp_server_permission_apply_record",
    ],
)
def test_bk_paas3_receives_permission_apply_record_resource_grant(resource_name, mocker):
    command = Command()
    definition = command.get_definition(
        define=[],
        file=str(Path(settings.BASE_DIR) / "data/apigw-definitions/bk-apigateway-definition.yaml"),
        namespace=command.default_namespace,
    )
    manager = mocker.Mock()

    command.do(manager, definition)

    paas_grants = [
        call.kwargs for call in manager.grant_permission.call_args_list if call.kwargs["target_app_code"] == "bk_paas3"
    ]
    assert len(paas_grants) == 1
    assert paas_grants[0]["grant_dimension"] == "resource"
    assert resource_name in paas_grants[0]["resource_names"]
