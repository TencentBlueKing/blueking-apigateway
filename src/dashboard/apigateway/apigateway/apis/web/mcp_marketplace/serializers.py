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

from typing import Any, Dict

from rest_framework import serializers

from apigateway.apps.mcp_server.constants import MCPServerProtocolTypeEnum, MCPServerStatusEnum
from apigateway.service.mcp.mcp_server import build_mcp_server_url


class MCPServerListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述"
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerListInputSLZ"


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


class MCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerListOutputSLZ"


class MCPServerToolOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
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

    class Meta:
        ref_name = "apigateway.apis.web.mcp_marketplace.serializers.MCPServerRetrieveOutputSLZ"

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
