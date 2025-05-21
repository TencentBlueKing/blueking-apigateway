#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#

from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway, Stage
from apigateway.utils.time import NeverExpiresTime

from .constants import (
    MCPServerAppPermissionApplyExpireDaysEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerStatusEnum,
)


class MCPServer(TimestampedModelMixin, OperatorModelMixin):
    name = models.CharField(max_length=64, unique=True)
    description = models.CharField(max_length=512, blank=True, null=True)

    gateway = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)

    is_public = models.BooleanField(default=False)

    _labels = models.CharField(db_column="labels", max_length=1024, blank=True, null=True, default="")
    _resource_names = models.CharField(db_column="resource_names", max_length=1024, blank=True, null=True, default="")

    status = models.IntegerField(choices=MCPServerStatusEnum.get_choices())

    def __str__(self):
        return f"<MCPServer: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = "MCPServer"
        verbose_name_plural = "MCPServer"
        db_table = "mcp_server"

    @property
    def labels(self) -> List[str]:
        if not self._labels:
            return []
        return self._labels.split(";")

    @labels.setter
    def labels(self, value: List[str]):
        self._labels = ";".join(value)

    @property
    def resource_names(self) -> List[str]:
        if not self._resource_names:
            return []
        return self._resource_names.split(";")

    @resource_names.setter
    def resource_names(self, value: List[str]):
        self._resource_names = ";".join(value)

    @property
    def tools_count(self) -> int:
        return len(self.resource_names)

    @property
    def is_active(self) -> bool:
        return self.status == MCPServerStatusEnum.ACTIVE.value


class MCPServerAppPermission(TimestampedModelMixin, OperatorModelMixin):
    bk_app_code = models.CharField(max_length=32)
    mcp_server = models.ForeignKey(MCPServer, on_delete=models.CASCADE)
    expires = models.DateTimeField(
        default=NeverExpiresTime.time, blank=True, null=True, help_text=_("默认过期时间为永久")
    )
    grant_type = models.CharField(
        max_length=16, choices=MCPServerAppPermissionGrantTypeEnum.get_choices(), db_index=True
    )

    def __str__(self):
        return f"<MCPServerAppPermission: {self.pk}>"

    class Meta:
        verbose_name = _("MCPServer 已授权应用")
        verbose_name_plural = _("MCPServer 已授权应用")
        unique_together = ("bk_app_code", "mcp_server")
        db_table = "mcp_server_app_permission"


class MCPServerAppPermissionApply(TimestampedModelMixin, OperatorModelMixin):
    bk_app_code = models.CharField(max_length=32, db_index=True)
    mcp_server = models.ForeignKey(MCPServer, on_delete=models.CASCADE)
    applied_by = models.CharField(max_length=32)
    applied_time = models.DateTimeField()
    reason = models.CharField(max_length=512, blank=True, default="")
    expire_days = models.IntegerField(default=MCPServerAppPermissionApplyExpireDaysEnum.FOREVER.value)
    handled_by = models.CharField(max_length=32, blank=True, default="")
    handled_time = models.DateTimeField(blank=True, null=True)
    comment = models.CharField(max_length=512, blank=True, default="")
    status = models.CharField(max_length=16, choices=MCPServerAppPermissionApplyStatusEnum.get_choices())

    def __str__(self):
        return f"<MCPServerAppPermissionApply: {self.pk}>"

    class Meta:
        verbose_name = _("MCPServer 应用申请审批")
        verbose_name_plural = _("MCPServer 应用申请审批")
        db_table = "mcp_server_app_permission_apply"
        indexes = [
            models.Index(fields=["mcp_server", "status"]),
        ]
