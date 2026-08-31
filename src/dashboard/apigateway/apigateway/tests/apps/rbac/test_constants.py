from apigateway.apps.rbac.constants import GatewayRoleEnum


def test_gateway_role_enum_values():
    assert GatewayRoleEnum.get_values() == ["administrator", "operator"]
    assert [value for value, _ in GatewayRoleEnum.get_choices()] == [
        "administrator",
        "operator",
    ]
