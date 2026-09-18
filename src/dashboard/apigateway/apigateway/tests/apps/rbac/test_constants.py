from apigateway.apps.rbac.constants import (
    GATEWAY_MEMBER_EXPIRE_DAYS,
    GATEWAY_ROLE_ACTIONS,
    GatewayActionEnum,
    GatewayRoleEnum,
)
from apigateway.biz.iam.constants import BK_IAM_V4_SYSTEM_ID
from apigateway.components.bkiam import BK_IAM_V4_SYSTEM_ID as CLIENT_SYSTEM_ID


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


def test_iam_v4_system_id_is_fixed():
    assert BK_IAM_V4_SYSTEM_ID == "bk_apigateway"
    assert BK_IAM_V4_SYSTEM_ID == CLIENT_SYSTEM_ID


def test_gateway_member_expire_days_is_fixed():
    assert GATEWAY_MEMBER_EXPIRE_DAYS == 365
