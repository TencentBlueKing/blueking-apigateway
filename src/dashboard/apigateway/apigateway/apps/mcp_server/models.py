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

from typing import ClassVar, Dict, List, Tuple

from django.db import models
from django.utils.translation import gettext_lazy as _

from apigateway.apps.mcp_server import managers
from apigateway.common.mixins.models import OperatorModelMixin, TimestampedModelMixin
from apigateway.core.models import Gateway, Stage
from apigateway.utils.time import NeverExpiresTime

from .constants import (
    MCPServerAppPermissionApplyExpireDaysEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerExtendTypeEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)

# 工具名分隔符：resource_name@tool_name
TOOL_NAME_SEPARATOR = "@"


def parse_resource_name_with_tool(resource_name_with_tool: str) -> Tuple[str, str]:
    """解析带有工具名的资源名称

    格式: resource_name 或 resource_name@tool_name

    Args:
        resource_name_with_tool: 资源名称，可能包含工具名

    Returns:
        (resource_name, tool_name) 元组，如果没有工具名则 tool_name 为空字符串
    """
    if TOOL_NAME_SEPARATOR in resource_name_with_tool:
        parts = resource_name_with_tool.split(TOOL_NAME_SEPARATOR, 1)
        return parts[0], parts[1]
    return resource_name_with_tool, ""


def convert_resource_names_to_storage_format(resource_names: List[Dict[str, str]]) -> List[str]:
    """将前端传入的资源名称列表转换为存储格式

    输入格式: [{"resource_name": "xxx", "tool_name": "yyy"}, ...]
    输出格式: ["xxx@yyy", ...] 或 ["xxx", ...] (如果 tool_name 为空)
    """
    result = []
    for item in resource_names:
        resource_name = item["resource_name"]
        tool_name = item.get("tool_name", "")
        if tool_name:
            result.append(f"{resource_name}{TOOL_NAME_SEPARATOR}{tool_name}")
        else:
            result.append(resource_name)
    return result


def convert_resource_names_from_storage_format(resource_names: List[str]) -> List[Dict[str, str]]:
    """将存储格式的资源名称列表转换为前端展示格式

    输入格式: ["xxx@yyy", ...] 或 ["xxx", ...]
    输出格式: [{"resource_name": "xxx", "tool_name": "yyy"}, ...]
    """
    result = []
    for name in resource_names:
        resource_name, tool_name = parse_resource_name_with_tool(name)
        result.append({"resource_name": resource_name, "tool_name": tool_name})
    return result


def get_pure_resource_names(resource_names: List[str]) -> List[str]:
    """从资源名称列表中提取纯资源名称（去除工具名部分）

    Args:
        resource_names: 资源名称列表，可能包含 resource_name@tool_name 格式

    Returns:
        纯资源名称列表
    """
    return [parse_resource_name_with_tool(name)[0] for name in resource_names]


def get_resource_name_tool_map(resource_names: List[str]) -> Dict[str, str]:
    """构建资源名称到工具名的映射

    Args:
        resource_names: 资源名称列表，可能包含 resource_name@tool_name 格式

    Returns:
        {resource_name: tool_name} 映射，如果没有工具名则值为空字符串
    """
    return dict(parse_resource_name_with_tool(name) for name in resource_names)


class MCPServer(TimestampedModelMixin, OperatorModelMixin):
    name = models.CharField(max_length=64, unique=True)
    title = models.CharField(max_length=128, blank=True, default="", help_text="MCPServer 中文名/显示名称")
    description = models.TextField(blank=True, null=True)

    gateway = models.ForeignKey(Gateway, on_delete=models.CASCADE)
    stage = models.ForeignKey(Stage, on_delete=models.CASCADE)

    is_public = models.BooleanField(default=False)

    _labels = models.CharField(db_column="labels", max_length=1024, blank=True, null=True, default="")
    _resource_names = models.TextField(db_column="resource_names", blank=True, null=True, default="")

    status = models.IntegerField(choices=MCPServerStatusEnum.get_choices())
    protocol_type = models.CharField(
        max_length=32,
        choices=MCPServerProtocolTypeEnum.get_choices(),
        default=MCPServerProtocolTypeEnum.SSE.value,
        help_text="MCP 协议类型",
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
    def resource_names_raw(self) -> List[str]:
        """获取原始存储格式的资源名称列表（包含工具名）

        返回格式: ["xxx@yyy", ...] 或 ["xxx", ...]
        """
        if not self._resource_names:
            return []
        return self._resource_names.split(";")

    @resource_names_raw.setter
    def resource_names_raw(self, value: List[str]):
        """设置原始存储格式的资源名称列表

        输入格式: ["xxx@yyy", ...] 或 ["xxx", ...]
        """
        self._resource_names = ";".join(value)

    @property
    def resource_names(self) -> List[str]:
        """获取纯资源名称列表（去除工具名部分）

        返回格式: ["xxx", "yyy", ...]
        注意：此属性保持向后兼容，只返回纯资源名称
        """
        return get_pure_resource_names(self.resource_names_raw)

    @resource_names.setter
    def resource_names(self, value: List[str]):
        """设置存储格式的资源名称列表（保持与历史行为兼容）

        注意：
        - getter 返回的是"纯资源名"（不包含工具名），例如 ["xxx", "yyy", ...]
        - setter 接受的是"存储格式"的资源名（可能包含工具名），例如 ["xxx@tool", "yyy", ...]

        为避免歧义，新的代码如果需要直接读写存储格式，建议使用：
        - `resource_names_raw`（List[str]，如 ["xxx@tool", "yyy", ...]）
        - 或 `resource_names_with_tool`（List[Dict[str, str]]，如 {"resource_name": "xxx", "tool_name": "tool"}）
        """
        self._resource_names = ";".join(value)

    @property
    def resource_names_with_tool(self) -> List[Dict[str, str]]:
        """获取带工具名的资源名称列表（前端展示格式）

        返回格式: [{"resource_name": "xxx", "tool_name": "yyy"}, ...]
        """
        return convert_resource_names_from_storage_format(self.resource_names_raw)

    @resource_names_with_tool.setter
    def resource_names_with_tool(self, value: List[Dict[str, str]]):
        """设置带工具名的资源名称列表（前端输入格式）

        输入格式: [{"resource_name": "xxx", "tool_name": "yyy"}, ...]
        """
        self._resource_names = ";".join(convert_resource_names_to_storage_format(value))

    @property
    def resource_name_tool_map(self) -> Dict[str, str]:
        """获取资源名称到工具名的映射

        返回格式: {"resource_name": "tool_name", ...}
        """
        return get_resource_name_tool_map(self.resource_names_raw)

    @property
    def tool_names(self) -> List[str]:
        """获取工具名列表（与 resource_names 顺序对应）

        返回格式: ["tool1", "", "tool3", ...]
        如果资源没有自定义工具名，则对应位置为空字符串
        """
        return [parse_resource_name_with_tool(name)[1] for name in self.resource_names_raw]

    def update_resource_names(self, resource_names_with_tool: List[Dict[str, str]]) -> None:
        """更新资源名称列表

        此方法封装了资源名称的更新逻辑，包括格式转换。

        Args:
            resource_names_with_tool: 前端格式的资源名称列表
                格式: [{"resource_name": "xxx", "tool_name": "yyy"}, ...]
        """
        self._resource_names = ";".join(convert_resource_names_to_storage_format(resource_names_with_tool))

        self._resource_names = ";".join(convert_resource_names_to_storage_format(resource_names_with_tool))

    def remove_deleted_resources(self, deleted_resource_names: set) -> bool:
        """移除已删除的资源

        Args:
            deleted_resource_names: 需要删除的纯资源名称集合

        Returns:
            是否有资源被移除
        """
        if not deleted_resource_names:
            return False

        new_resource_names_raw = [
            name
            for name in self.resource_names_raw
            if parse_resource_name_with_tool(name)[0] not in deleted_resource_names
        ]

        if len(new_resource_names_raw) == len(self.resource_names_raw):
            return False

        self._resource_names = ";".join(new_resource_names_raw)
        return True

    @property
    def tools_count(self) -> int:
        return len(self.resource_names_raw)

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
