from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.utils.translation import gettext_lazy as _


class GatewayRoleEnum(StructuredEnum):
    ADMINISTRATOR = EnumField("administrator", _("管理员"))
    OPERATOR = EnumField("operator", _("运营者"))
