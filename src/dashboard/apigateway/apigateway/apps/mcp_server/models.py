#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from typing import ClassVar, Dict, List

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.mcp_server import managers
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway, Stage
from apigateway.utils.time import NeverExpiresTime

from .constants import (
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerAppPermissionApplyExpireDaysEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerExtendTypeEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)

# 工具名分隔符：resource_name@tool_name
TOOL_NAME_SEPARATOR = "@"
POSITION_RESOURCE_NAME = 0
POSITION_TOOL_NAME = 1


class MCPServerCategory(TimestampedModelMixin, OperatorModelMixin):
    """MCPServer 分类表"""

    name = models.CharField(max_length=64, unique=True, help_text=_("分类名称（英文标识）"))
    display_name = models.CharField(max_length=128, help_text=_("分类显示名称"))
    description = models.TextField(blank=True, default="", help_text=_("分类描述"))
    is_active = models.BooleanField(default=True, help_text=_("是否启用"))
    sort_order = models.IntegerField(default=0, help_text=_("排序顺序，数字越小越靠前"))

    def __str__(self):
        return f"<MCPServerCategory: {self.pk}/{self.name}>"

    class Meta:
        verbose_name = _("MCPServer 分类")
        verbose_name_plural = _("MCPServer 分类")
        db_table = "mcp_server_category"
        ordering = ["sort_order", "id"]

    @property
    def is_official(self) -> bool:
        """是否为官方分类"""
        return self.name == OFFICIAL_MCP_CATEGORY_NAME

    @property
    def is_featured(self) -> bool:
        """是否为精选分类"""
        return self.name == FEATURED_MCP_CATEGORY_NAME

    @property
    def is_special_category(self) -> bool:
        """是否为特殊分类（官方、精选）"""
        return self.is_official or self.is_featured


class MCPServer(TimestampedModelMixin, OperatorModelMixin):
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=128, blank=True, default="", help_text="MCPServer 中文名/显示名称")
    description = models.TextField(blank=True, null=True)

    gateway = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)

    is_public = models.BooleanField(default=False)

    _labels = models.CharField(db_column="labels", max_length=1024, blank=True, null=True, default="")
    # db: resource_name_1;resource_name_2@tool_name_2;resource_name_3@tool_name_3
    # would parse to resource_names and tool_names, if tool_name is empty, it will be the same as resource_name
    # resource_names: [resource_name_1, resource_name_2, resource_name_3]
    # tool_names: [resource_name_1, tool_name_2, tool_name_3]
    _resource_names = models.TextField(db_column="resource_names", blank=True, null=True, default="")

    status = models.IntegerField(choices=MCPServerStatusEnum.get_choices())
    protocol_type = models.CharField(
        max_length=32,
        choices=MCPServerProtocolTypeEnum.get_choices(),
        default=MCPServerProtocolTypeEnum.SSE.value,
        help_text="MCP 协议类型",
    )

    oauth2_enabled = models.BooleanField(
        default=False,
        help_text=_("是否开启 OAuth2 认证，开启后自动为 bk_app_code=public 授权"),
    )

    # 分类关联（多对多关系）
    categories = models.ManyToManyField(
        MCPServerCategory,
        blank=True,
        related_name="mcp_servers",
        help_text=_("MCPServer 所属分类"),
    )

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
    def is_active(self) -> bool:
        return self.status == MCPServerStatusEnum.ACTIVE.value

    def _parse_resource_names_to_part(self, position: int) -> List[str]:
        """
        db: resource_name_1;resource_name_2@tool_name_2;resource_name_3@tool_name_3
        position: 0 is resource_names list: [resource_name_1, resource_name_2, resource_name_3]
        position: 1 is tool_names list:     [resource_name_1, tool_name_2, tool_name_3]
        """

        if not self._resource_names:
            return []

        result = []
        for i in self._resource_names.split(";"):
            if TOOL_NAME_SEPARATOR in i:
                result.append(i.split(TOOL_NAME_SEPARATOR)[position])
            else:
                result.append(i)
        return result

    @property
    def resource_names(self) -> List[str]:
        """获取纯资源名称列表（去除工具名部分）"""
        return self._parse_resource_names_to_part(POSITION_RESOURCE_NAME)

    @resource_names.setter
    def resource_names(self, value: List[str]):
        raise NotImplementedError(
            "Not supported, you should use update_resource_names or delete_resource_names instead"
        )

    def delete_resource_names(self, deleted_resource_names: set) -> bool:
        """移除已删除的资源

        Args:
            to_deleted_resource_names: 需要删除的纯资源名称集合

        Returns:
            是否有资源被移除
        """
        if not deleted_resource_names:
            return False

        current_resource_names = self.resource_names
        current_tool_names = self.tool_names

        result = []
        for index, resource_name in enumerate(current_resource_names):
            if resource_name in deleted_resource_names:
                continue

            tool_name = current_tool_names[index]
            if tool_name and tool_name != resource_name:
                result.append(f"{resource_name}{TOOL_NAME_SEPARATOR}{tool_name}")
            else:
                result.append(resource_name)

        self._resource_names = ";".join(result)
        return True

    @property
    def tool_names(self) -> List[str]:
        """获取工具名列表（与 resource_names 顺序对应）
        如果没有设置工具名，使用资源名
        """
        return self._parse_resource_names_to_part(POSITION_TOOL_NAME)

    @tool_names.setter
    def tool_names(self, value: List[str]):
        raise NotImplementedError(
            "Not supported, you should use update_resource_names or delete_resource_names instead"
        )

    @property
    def tools_count(self) -> int:
        return len(self.tool_names)

    def gen_tool_name_map(self) -> Dict[str, str]:
        """生成工具名称映射"""
        return dict(zip(self.resource_names, self.tool_names))

    def update_resource_names(self, resource_names: List[str], tool_names: List[str]) -> None:
        """更新资源名称列表

        Args:
            resource_names: 资源名称列表
            tool_names: 工具名称列表
        """
        if len(resource_names) != len(tool_names):
            raise ValueError("resource_names and tool_names length must be the same")

        result = []
        for resource_name, tool_name in zip(resource_names, tool_names):
            if tool_name and tool_name != resource_name:
                result.append(f"{resource_name}{TOOL_NAME_SEPARATOR}{tool_name}")
            else:
                result.append(resource_name)
        self._resource_names = ";".join(result)

    def get_category_names(self) -> List[str]:
        """获取分类名称列表"""
        return list(self.categories.filter(is_active=True).values_list("name", flat=True))

    def get_category_display_names(self) -> List[str]:
        """获取分类显示名称列表"""
        return list(self.categories.filter(is_active=True).values_list("display_name", flat=True))

    def is_official(self) -> bool:
        """是否为官方 MCPServer"""
        return self.categories.filter(name=OFFICIAL_MCP_CATEGORY_NAME, is_active=True).exists()

    def is_featured(self) -> bool:
        """是否为精选 MCPServer"""
        return self.categories.filter(name=FEATURED_MCP_CATEGORY_NAME, is_active=True).exists()


class MCPServerAppPermission(TimestampedModelMixin, OperatorModelMixin):
    bk_app_code = models.CharField(max_length=32)
    mcp_server = models.ForeignKey(MCPServer, on_delete=models.CASCADE)
    expires = models.DateTimeField(
        default=NeverExpiresTime.time, blank=True, null=True, help_text=_("默认过期时间为永久")
    )
    grant_type = models.CharField(
        max_length=16, choices=MCPServerAppPermissionGrantTypeEnum.get_choices(), db_index=True
    )
    objects: ClassVar[managers.MCPServerAppPermissionManager] = managers.MCPServerAppPermissionManager()

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
    is_deleted = models.BooleanField(default=False)
    objects: ClassVar[managers.MCPServerAppPermissionApplyManager] = managers.MCPServerAppPermissionApplyManager()

    def __str__(self):
        return f"<MCPServerAppPermissionApply: {self.pk}>"

    class Meta:
        verbose_name = _("MCPServer 应用申请审批")
        verbose_name_plural = _("MCPServer 应用申请审批")
        db_table = "mcp_server_app_permission_apply"
        indexes = [
            models.Index(fields=["mcp_server", "status"]),
        ]


class MCPServerExtend(TimestampedModelMixin, OperatorModelMixin):
    """MCPServer 扩展配置表"""

    mcp_server = models.ForeignKey(MCPServer, on_delete=models.CASCADE, related_name="extends")
    type = models.CharField(
        max_length=32, choices=MCPServerExtendTypeEnum.get_choices(), db_index=True, help_text=_("配置类型")
    )
    content = models.TextField(blank=True, default="", help_text=_("配置内容"))

    def __str__(self):
        return f"<MCPServerExtend: {self.pk}/{self.mcp_server_id}/{self.type}>"

    class Meta:
        verbose_name = _("MCPServer 扩展配置")
        verbose_name_plural = _("MCPServer 扩展配置")
        db_table = "mcp_server_extend"
        unique_together = ("mcp_server", "type")
