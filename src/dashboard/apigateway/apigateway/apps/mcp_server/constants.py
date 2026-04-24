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

from blue_krill.data_types.enum import EnumField, StructuredEnum
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class MCPServerStatusEnum(StructuredEnum):
    INACTIVE = EnumField(0, "已停用")
    ACTIVE = EnumField(1, "启用中")


class MCPServerAppPermissionApplyExpireDaysEnum(StructuredEnum):
    FOREVER = EnumField(0, label=_("永久"))


class MCPServerAppPermissionGrantTypeEnum(StructuredEnum):
    GRANT = EnumField("grant", label=_("授权"))
    APPLY = EnumField("apply", label=_("申请"))


class MCPServerAppPermissionApplyStatusEnum(StructuredEnum):
    APPROVED = EnumField("approved", label=_("通过"))
    REJECTED = EnumField("rejected", label=_("驳回"))
    PENDING = EnumField("pending", label=_("待审批"))


class MCPServerAppPermissionApplyProcessedStateEnum(StructuredEnum):
    PROCESSED = EnumField("processed", label=_("已处理"))
    UNPROCESSED = EnumField("unprocessed", label=_("未处理"))


class MCPServerPermissionStatusEnum(StructuredEnum):
    APPROVED = EnumField("approved", label="已审批")
    REJECTED = EnumField("rejected", label="已拒绝")
    PENDING = EnumField("pending", label="申请中")
    NEED_APPLY = EnumField("need_apply", label="待申请")
    OWNED = EnumField("owned", label="已申请，且未过期")


class MCPServerPermissionActionEnum(StructuredEnum):
    APPLY = EnumField("apply")
    RENEW = EnumField("renew")


class MCPServerLeastPrivilegeEnum(StructuredEnum):
    APPLICATION = EnumField("application")
    APPLICATION_AND_USER = EnumField("application_and_user")


class MCPServerExtendTypeEnum(StructuredEnum):
    """MCPServer 扩展配置类型"""

    USER_CUSTOM_DOC = EnumField("user_custom_doc", label=_("用户自定义文档"))
    PROMPTS = EnumField("prompts", label=_("Prompts 配置"))


class MCPServerProtocolTypeEnum(StructuredEnum):
    """MCPServer 协议类型"""

    SSE = EnumField("sse", label=_("SSE"))
    STREAMABLE_HTTP = EnumField("streamable_http", label=_("Streamable HTTP"))


class MCPAgentClientTypeEnum(StructuredEnum):
    """MCP Agent 客户端类型"""

    CODEBUDDY = EnumField("codebuddy", label="CodeBuddy")
    CURSOR = EnumField("cursor", label="Cursor")
    CLAUDE = EnumField("claude", label="Claude")
    VSCODE = EnumField("vscode", label="VSCode")
    AIDEV = EnumField("aidev", label="AIDev")


# MCP Agent 客户端 choices（不含 AIDev），供批量配置序列化器校验使用
MCP_AGENT_CLIENT_CHOICES_WITHOUT_AIDEV = [
    choice for choice in MCPAgentClientTypeEnum.get_choices() if choice[0] != MCPAgentClientTypeEnum.AIDEV.value
]

# MCP Server 配置工具的默认客户端类型列表（不含 AIDev）
_MCP_CONFIG_DEFAULT_CLIENT_TYPES = [
    MCPAgentClientTypeEnum.CODEBUDDY,
    MCPAgentClientTypeEnum.CURSOR,
    MCPAgentClientTypeEnum.CLAUDE,
    MCPAgentClientTypeEnum.VSCODE,
]


def get_mcp_config_agent_clients() -> list:
    """获取 MCP Server 配置工具的客户端列表，根据 AIDEV_AGENT_CREATE_URL 动态决定是否包含 AIDev"""
    clients = [{"name": member.value, "display_name": member.label} for member in _MCP_CONFIG_DEFAULT_CLIENT_TYPES]

    if getattr(settings, "AIDEV_AGENT_CREATE_URL", ""):
        clients.append(
            {"name": MCPAgentClientTypeEnum.AIDEV.value, "display_name": MCPAgentClientTypeEnum.AIDEV.label}
        )

    return clients


# MCPServer 分类名称常量 - 用于判断特殊分类
OFFICIAL_MCP_CATEGORY_NAME = "Official"
FEATURED_MCP_CATEGORY_NAME = "Featured"
# 默认分类名称 - 未设置分类时使用
UNCATEGORIZED_MCP_CATEGORY_NAME = "Uncategorized"
