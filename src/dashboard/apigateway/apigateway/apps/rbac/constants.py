from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _


class GatewayRoleEnum(StructuredEnum):
    ADMINISTRATOR = EnumField("administrator", _("管理员"))
    OPERATOR = EnumField("operator", _("运营者"))


class GatewayActionEnum(StructuredEnum):
    MANAGE_GATEWAY = EnumField("manage_gateway", _("管理网关"))
    OPERATE_GATEWAY = EnumField("operate_gateway", _("运营网关"))
    APPROVE_GATEWAY_PERMISSION = EnumField("approve_gateway_permission", _("管理网关权限"))


GATEWAY_ROLE_ACTIONS = {
    GatewayRoleEnum.ADMINISTRATOR.value: (
        GatewayActionEnum.MANAGE_GATEWAY.value,
        GatewayActionEnum.OPERATE_GATEWAY.value,
        GatewayActionEnum.APPROVE_GATEWAY_PERMISSION.value,
    ),
    GatewayRoleEnum.OPERATOR.value: (
        GatewayActionEnum.OPERATE_GATEWAY.value,
        GatewayActionEnum.APPROVE_GATEWAY_PERMISSION.value,
    ),
}
