from django.db import models

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway


class GatewayMember(TimestampedModelMixin, OperatorModelMixin):
    # Gateway members have no meaning after their gateway is deleted.
    gateway = models.ForeignKey(
        Gateway,
        db_column="api_id",
        on_delete=models.CASCADE,
        related_name="members",
    )
    username = models.CharField(max_length=64, db_index=True)
    role = models.CharField(max_length=32, choices=GatewayRoleEnum.get_choices())
    expires = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"<GatewayMember: {self.gateway_id}/{self.username}/{self.role}>"

    class Meta:
        db_table = "core_gateway_member"
        unique_together = ("gateway", "username")
