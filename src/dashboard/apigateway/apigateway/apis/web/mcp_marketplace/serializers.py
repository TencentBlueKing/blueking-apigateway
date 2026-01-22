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

from typing import Any, Dict, List

from rest_framework import serializers

from apigateway.apps.mcp_server.constants import (
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.service.mcp.mcp_server import build_mcp_server_url


class MCPServerCategoryOutputSLZ(serializers.Serializer):
    """MCPServer 分类输出序列化器"""

    id = serializers.IntegerField(read_only=True, help_text="分类 ID")
    name = serializers.CharField(read_only=True, help_text="分类名称（英文标识）")
    display_name = serializers.CharField(read_only=True, help_text="分类显示名称")
    description = serializers.CharField(read_only=True, help_text="分类描述")
    sort_order = serializers.IntegerField(read_only=True, help_text="排序顺序")
    mcp_server_count = serializers.SerializerMethodField(help_text="该分类下的 MCPServer 数量")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerCategoryOutputSLZ"

    def get_mcp_server_count(self, obj) -> int:
        """获取该分类下的 MCPServer 数量"""
        # 从 context 中获取统计数据，如果没有则返回 0
        category_stats = self.context.get("category_stats", {})
        return category_stats.get(obj.id, 0)


class MCPServerListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述"
    )
    categories = serializers.CharField(
        allow_blank=True, required=False, help_text="分类筛选，支持单个或多个分类名称，多个分类以逗号分隔"
    )
    order_by = serializers.ChoiceField(
        choices=[
            ("updated_time", "按更新时间排序"),
            ("-updated_time", "按更新时间倒序"),
            ("created_time", "按创建时间排序"),
            ("-created_time", "按创建时间倒序"),
            ("name", "按名称字母顺序排序"),
            ("-name", "按名称字母倒序排序"),
        ],
        default="-updated_time",
        required=False,
        help_text="排序方式",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerListInputSLZ"

    def validate_categories(self, value):
        """解析分类参数，支持多个分类名称（逗号分隔）"""
        if not value:
            return []
        # 解析逗号分隔的分类名称，去除空白
        return [cat.strip() for cat in value.split(",") if cat.strip()]


def _get_active_categories_from_prefetch(obj) -> List:
    """
    从预加载的数据中获取激活的分类列表，避免 N+1 查询。

    如果已经通过 prefetch_related 预加载了 categories，则在内存中过滤和排序；
    否则回退到数据库查询。
    """
    # 使用预取的 categories 关系数据，在内存中过滤和排序
    return sorted(
        (cat for cat in obj.categories.all() if cat.is_active),
        key=lambda cat: cat.sort_order,
    )


class MCPServerBaseOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 中文名/显示名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    is_public = serializers.BooleanField(read_only=True, help_text="MCPServer 是否公开")

    labels = serializers.ListField(read_only=True, help_text="MCPServer 标签")
    resource_names = serializers.ListField(read_only=True, help_text="MCPServer 资源名称")
    tool_names = serializers.ListField(read_only=True, help_text="MCPServer 工具名称")

    status = serializers.ChoiceField(
        read_only=True, help_text="MCPServer 状态", choices=MCPServerStatusEnum.get_choices()
    )

    protocol_type = serializers.ChoiceField(
        read_only=True,
        help_text="MCPServer 协议类型",
        choices=MCPServerProtocolTypeEnum.get_choices(),
    )

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")
    gateway = serializers.SerializerMethodField(help_text="MCPServer 网关")

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")
    prompts_count = serializers.SerializerMethodField(help_text="MCPServer Prompts 数量")
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")

    updated_time = serializers.DateTimeField(read_only=True, help_text="MCPServer 更新时间")
    created_time = serializers.DateTimeField(read_only=True, help_text="MCPServer 创建时间")

    # 分类信息
    categories = serializers.SerializerMethodField(help_text="MCPServer 分类列表")
    is_official = serializers.SerializerMethodField(help_text="是否为官方")
    is_featured = serializers.SerializerMethodField(help_text="是否为精选")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerBaseOutputSLZ"

    def get_stage(self, obj) -> Dict[str, Any]:
        return self.context["stages"][obj.stage.id]

    def get_gateway(self, obj) -> Dict[str, Any]:
        return self.context["gateways"][obj.gateway.id]

    def get_url(self, obj) -> str:
        return build_mcp_server_url(obj.name, obj.protocol_type)

    def get_prompts_count(self, obj) -> int:
        prompts_count_map = self.context.get("prompts_count_map", {})
        return prompts_count_map.get(obj.id, 0)

    def get_categories(self, obj):
        """获取分类信息，利用预加载的数据避免 N+1 查询"""
        active_categories = _get_active_categories_from_prefetch(obj)
        return MCPServerCategoryOutputSLZ(active_categories, many=True).data

    def get_is_official(self, obj) -> bool:
        """是否为官方，利用预加载的数据避免 N+1 查询"""
        active_categories = _get_active_categories_from_prefetch(obj)
        return any(cat.name == OFFICIAL_MCP_CATEGORY_NAME for cat in active_categories)

    def get_is_featured(self, obj) -> bool:
        """是否为精选，利用预加载的数据避免 N+1 查询"""
        active_categories = _get_active_categories_from_prefetch(obj)
        return any(cat.name == FEATURED_MCP_CATEGORY_NAME for cat in active_categories)


class MCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerListOutputSLZ"


class MCPServerToolOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    tool_name = serializers.SerializerMethodField(help_text="工具名称（重命名后的名称）")
    description = serializers.CharField(read_only=True, help_text="资源描述")
    method = serializers.CharField(read_only=True, help_text="资源前端请求方法")
    path = serializers.CharField(read_only=True, help_text="资源前端请求路径")

    verified_user_required = serializers.BooleanField(read_only=True, help_text="是否需要认证用户")
    verified_app_required = serializers.BooleanField(read_only=True, help_text="是否需要认证应用")
    resource_perm_required = serializers.BooleanField(read_only=True, help_text="是否验证应用访问资源的权限")
    allow_apply_permission = serializers.BooleanField(read_only=True, help_text="是否需要申请权限")
    labels = serializers.SerializerMethodField(help_text="资源标签列表")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerToolOutputSLZ"

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])

    def get_tool_name(self, obj) -> str:
        """获取工具名称（重命名后的名称）"""
        tool_name_map = self.context.get("tool_name_map", {})
        return tool_name_map.get(obj.name, "")


class MCPServerPromptOutputSLZ(serializers.Serializer):
    """单个 Prompt 项的输出序列化器，与 MCPServerPromptItemSLZ 保持一致"""

    id = serializers.IntegerField(read_only=True, help_text="Prompt ID（第三方平台的唯一标识）")
    name = serializers.CharField(read_only=True, help_text="Prompt 名称")
    code = serializers.CharField(read_only=True, help_text="Prompt 标识码")
    content = serializers.CharField(read_only=True, allow_blank=True, default="", help_text="Prompt 内容")
    updated_time = serializers.CharField(read_only=True, allow_blank=True, default="", help_text="Prompt 更新时间")
    updated_by = serializers.CharField(read_only=True, allow_blank=True, default="", help_text="Prompt 更新人")
    labels = serializers.ListField(
        child=serializers.CharField(), read_only=True, default=list, help_text="Prompt 标签列表"
    )
    is_public = serializers.BooleanField(read_only=True, default=False, help_text="Prompt 是否公开")
    space_code = serializers.CharField(read_only=True, allow_blank=True, default="", help_text="Prompt 所在空间标识")
    space_name = serializers.CharField(read_only=True, allow_blank=True, default="", help_text="Prompt 所在空间名称")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerPromptOutputSLZ"


class MCPServerRetrieveOutputSLZ(MCPServerBaseOutputSLZ):
    guideline = serializers.CharField(read_only=True, help_text="MCPServer 使用指南")
    tools = serializers.ListField(child=MCPServerToolOutputSLZ(), help_text="MCPServer 工具列表")
    prompts = serializers.SerializerMethodField(help_text="MCPServer Prompts 列表")
    maintainers = serializers.ListField(child=serializers.CharField(), help_text="MCPServer 维护者")
    user_custom_doc = serializers.SerializerMethodField(help_text="用户自定义文档")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerRetrieveOutputSLZ"

    def get_user_custom_doc(self, obj) -> str:
        return self.context.get("user_custom_doc", "")

    def get_prompts(self, obj):
        prompts = self.context.get("prompts", [])
        # 私有的 prompt 将 content 设置为空
        result = []
        for p in prompts:
            prompt_data = dict(p)
            if not prompt_data.get("is_public", False):
                prompt_data["content"] = ""
            result.append(prompt_data)
        return MCPServerPromptOutputSLZ(result, many=True).data


class MCPServerToolDocOutputSLZ(serializers.Serializer):
    type = serializers.CharField(read_only=True, help_text="文档类型")
    content = serializers.CharField(read_only=True, help_text="文档内容")
    updated_time = serializers.DateTimeField(read_only=True, help_text="文档更新时间")
    schema = serializers.DictField(read_only=True, help_text="资源 schema")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerToolDocOutputSLZ"
