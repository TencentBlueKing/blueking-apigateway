from apigateway.apps.rbac.constants import GATEWAY_ROLE_ACTIONS, GatewayActionEnum, GatewayRoleEnum


def test_gateway_role_enum_values():
    assert GatewayRoleEnum.get_values() == ["administrator", "operator"]
    assert [value for value, _ in GatewayRoleEnum.get_choices()] == [
        "administrator",
        "operator",
    ]


def test_gateway_action_enum_and_role_actions():
    assert GatewayActionEnum.get_values() == [
        "manage_gateway",
        "operate_gateway",
        "approve_gateway_permission",
    ]
    assert {
        GatewayRoleEnum.ADMINISTRATOR.value: tuple(GatewayActionEnum.get_values()),
        GatewayRoleEnum.OPERATOR.value: (
            GatewayActionEnum.OPERATE_GATEWAY.value,
            GatewayActionEnum.APPROVE_GATEWAY_PERMISSION.value,
        ),
    } == GATEWAY_ROLE_ACTIONS
