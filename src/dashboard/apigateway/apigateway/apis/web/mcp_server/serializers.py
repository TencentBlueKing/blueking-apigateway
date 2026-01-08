#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

import logging
from typing import Any, Dict, List

from django.utils.translation import gettext_lazy as _
from rest_framework import serializers

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyProcessedStateEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermissionApply,
)
from apigateway.biz.mcp_server.prompt import MCPServerPromptHandler
from apigateway.biz.validators import BKAppCodeValidator, MCPServerHandler, MCPServerValidator
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.service.mcp.mcp_server import build_mcp_server_url

logger = logging.getLogger(__name__)


def _fill_prompts_content(prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    从第三方接口批量获取 prompts 的 content 字段，确保数据与第三方一致

    不管本地是否有 content，都会从第三方接口获取最新的 content 进行覆盖。
    如果第三方接口调用失败，会记录日志但不会阻止操作继续。
    """
    if not prompts:
        return prompts

    # 获取所有 prompt ids
    prompt_ids = [p["id"] for p in prompts]

    # 批量获取 content
    try:
        remote_prompts = MCPServerPromptHandler.fetch_remote_prompts_by_ids(prompt_ids)
    except Exception:
        logger.exception("Failed to fetch prompts content from remote API, prompt_ids=%s", prompt_ids)
        return prompts

    # 构建 id -> content 映射
    content_map = {p["id"]: p.get("content", "") for p in remote_prompts}

    # 用第三方的 content 覆盖本地数据
    for prompt in prompts:
        if prompt["id"] in content_map:
            prompt["content"] = content_map[prompt["id"]]

    return prompts


class MCPServerPromptItemSLZ(serializers.Serializer):
    """单个 Prompt 项的序列化器"""

    id = serializers.IntegerField(required=True, help_text="Prompt ID（第三方平台的唯一标识）")
    name = serializers.CharField(required=True, help_text="Prompt 名称")
    code = serializers.CharField(required=True, help_text="Prompt 标识码")
    content = serializers.CharField(required=False, allow_blank=True, default="", help_text="Prompt 内容")
    updated_time = serializers.CharField(required=False, allow_blank=True, default="", help_text="Prompt 更新时间")
    updated_by = serializers.CharField(required=False, allow_blank=True, default="", help_text="Prompt 更新人")
    labels = serializers.ListField(
        child=serializers.CharField(), required=False, default=list, help_text="Prompt 标签列表"
    )
    is_public = serializers.BooleanField(required=False, default=False, help_text="Prompt 是否公开")
    space_code = serializers.CharField(required=False, allow_blank=True, default="", help_text="Prompt 所在空间标识")
    space_name = serializers.CharField(required=False, allow_blank=True, default="", help_text="Prompt 所在空间名称")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerPromptItemSLZ"


class MCPServerResourceNameInputItemSLZ(serializers.Serializer):
    """资源名称输入项序列化器，支持工具重命名"""

    resource_name = serializers.CharField(required=True, help_text="资源名称")
    tool_name = serializers.CharField(
        required=False, allow_blank=True, default="", help_text="工具名称（重命名后的名称）"
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerResourceNameInputItemSLZ"


class MCPServerResourceNameOutputItemSLZ(serializers.Serializer):
    """资源名称输出项序列化器"""

    resource_name = serializers.CharField(read_only=True, help_text="资源名称")
    tool_name = serializers.CharField(read_only=True, help_text="工具名称（重命名后的名称）")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerResourceNameOutputItemSLZ"


class MCPServerCreateInputSLZ(serializers.ModelSerializer):
    stage_id = serializers.IntegerField(help_text="Stage ID")
    labels = serializers.ListField(child=serializers.CharField(), required=False, help_text="MCPServer 标签列表")
    resource_names = serializers.ListField(
        child=MCPServerResourceNameInputItemSLZ(), required=True, help_text="MCPServer 资源名称列表"
    )
    name = serializers.CharField(required=True, help_text="MCPServer 名称", max_length=64)
    title = serializers.CharField(
        required=False, allow_blank=True, help_text="MCPServer 中文名/显示名称", max_length=128
    )
    description = serializers.CharField(required=True, allow_blank=False, help_text="MCPServer 描述", max_length=512)
    prompts = serializers.ListField(
        child=MCPServerPromptItemSLZ(), required=False, default=list, help_text="Prompts 列表"
    )
    protocol_type = serializers.ChoiceField(
        choices=MCPServerProtocolTypeEnum.get_choices(),
        required=False,
        default=MCPServerProtocolTypeEnum.SSE.value,
        help_text="MCPServer 协议类型",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerCreateInputSLZ"
        model = MCPServer
        fields = (
            "name",
            "title",
            "description",
            "stage_id",
            "is_public",
            "labels",
            "resource_names",
            "prompts",
            "protocol_type",
        )
        lookup_field = "id"
        validators = [MCPServerValidator()]

    def validate_resource_names(self, resource_names):
        """验证资源名称列表"""
        if len(resource_names) == 0:
            raise serializers.ValidationError(_("资源名称列表不能为空"))

        # 验证 resource_name 不能重复
        pure_resource_names = [item["resource_name"] for item in resource_names]
        if len(pure_resource_names) != len(set(pure_resource_names)):
            raise serializers.ValidationError(_("资源名称不能重复"))

        # 验证 tool_name 不能重复（非空的 tool_name）
        tool_names = [item.get("tool_name", "") for item in resource_names if item.get("tool_name")]
        if len(tool_names) != len(set(tool_names)):
            raise serializers.ValidationError(_("工具名称不能重复"))

        # 返回原始格式，由 model 层处理转换
        return resource_names

    def create(self, validated_data):
        prompts = validated_data.pop("prompts", [])
        resource_names = validated_data.pop("resource_names")

        validated_data["gateway_id"] = self.context["gateway"].id
        validated_data["created_by"] = self.context["created_by"]
        validated_data["status"] = self.context["status"]

        # 创建实例并设置资源名称，一次性保存
        instance = MCPServer(**validated_data)
        instance.resource_names_with_tool = resource_names
        instance.save()

        # 保存 prompts
        if prompts:
            # 确保 content 是最新的
            prompts = _fill_prompts_content(prompts)
            MCPServerHandler.save_prompts(
                mcp_server_id=instance.id,
                prompts=prompts,
                username=self.context["created_by"],
            )

        return instance


class MCPServerBaseOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 中文名/显示名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    is_public = serializers.BooleanField(read_only=True, help_text="MCPServer 是否公开")

    labels = serializers.ListField(read_only=True, help_text="MCPServer 标签")
    resource_names = MCPServerResourceNameOutputItemSLZ(
        many=True, read_only=True, source="resource_names_with_tool", help_text="MCPServer 资源名称列表"
    )

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")

    status = serializers.ChoiceField(
        read_only=True, help_text="MCPServer 状态", choices=MCPServerStatusEnum.get_choices()
    )

    protocol_type = serializers.ChoiceField(
        read_only=True, help_text="MCP 协议类型", choices=MCPServerProtocolTypeEnum.get_choices()
    )

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")

    updated_time = serializers.DateTimeField(read_only=True, help_text="MCPServer 更新时间")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerBaseOutputSLZ"

    def get_stage(self, obj) -> Dict[str, Any]:
        return self.context["stages"][obj.stage.id]

    def get_url(self, obj) -> str:
        return build_mcp_server_url(obj.name, obj.protocol_type)


class MCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    prompts_count = serializers.SerializerMethodField(help_text="Prompts 数量")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerListOutputSLZ"

    def get_prompts_count(self, obj) -> int:
        prompts_count_map = self.context.get("prompts_count_map", {})
        return prompts_count_map.get(obj.id, 0)


class MCPServerRetrieveOutputSLZ(MCPServerBaseOutputSLZ):
    prompts = serializers.SerializerMethodField(help_text="Prompts 列表")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRetrieveOutputSLZ"

    def get_prompts(self, obj):
        return self.context.get("prompts", [])


class MCPServerUpdateInputSLZ(serializers.ModelSerializer):
    labels = serializers.ListField(child=serializers.CharField(), required=False, help_text="MCPServer 标签列表")
    resource_names = serializers.ListField(
        child=MCPServerResourceNameInputItemSLZ(), required=False, help_text="MCPServer 资源名称列表"
    )
    title = serializers.CharField(
        required=False, allow_blank=True, help_text="MCPServer 中文名/显示名称", max_length=128
    )
    description = serializers.CharField(required=True, allow_blank=False, help_text="MCPServer 描述", max_length=512)
    prompts = serializers.ListField(child=MCPServerPromptItemSLZ(), required=False, help_text="Prompts 列表")
    protocol_type = serializers.ChoiceField(
        choices=MCPServerProtocolTypeEnum.get_choices(),
        required=False,
        help_text="MCP 协议类型",
    )

    def validate_resource_names(self, resource_names):
        """验证资源名称列表"""
        if resource_names is not None:
            if len(resource_names) == 0:
                raise serializers.ValidationError(_("资源名称列表不能为空"))
            valid_resource_names = self.context["valid_resource_names"]

            # 验证 resource_name 不能重复
            pure_resource_names = [item["resource_name"] for item in resource_names]
            if len(pure_resource_names) != len(set(pure_resource_names)):
                raise serializers.ValidationError(_("资源名称不能重复"))

            for item in resource_names:
                pure_resource_name = item["resource_name"]
                if pure_resource_name not in valid_resource_names:
                    raise serializers.ValidationError(
                        _("资源名称列表非法，请检查当前环境发布的最新版本中对应资源名称是否存在")
                        + f"resource_name={pure_resource_name}"
                    )

            # 验证 tool_name 不能重复（非空的 tool_name）
            tool_names = [item.get("tool_name", "") for item in resource_names if item.get("tool_name")]
            if len(tool_names) != len(set(tool_names)):
                raise serializers.ValidationError(_("工具名称不能重复"))

        # 返回原始格式，由 model 层处理转换
        return resource_names

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateInputSLZ"
        model = MCPServer
        fields = ("title", "description", "is_public", "labels", "resource_names", "prompts", "protocol_type")
        lookup_field = "id"

    def update(self, instance, validated_data):
        prompts = validated_data.pop("prompts", None)
        resource_names = validated_data.pop("resource_names", None)

        # 更新普通字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 如果传入了 resource_names，使用 model 层方法更新
        if resource_names is not None:
            instance.update_resource_names(resource_names)

        # 一次性保存所有更改
        instance.save()

        # 如果传入了 prompts，则更新
        if prompts is not None:
            prompts = _fill_prompts_content(prompts)
            MCPServerHandler.save_prompts(
                mcp_server_id=instance.id,
                prompts=prompts,
                username=self.context.get("username", ""),
            )

        return instance


class MCPServerUpdateStatusInputSLZ(serializers.ModelSerializer):
    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateStatusInputSLZ"
        model = MCPServer
        fields = ("status",)
        lookup_field = "id"

    def validate_status(self, status):
        if status == MCPServerStatusEnum.ACTIVE.value:
            if self.instance.gateway.status == GatewayStatusEnum.INACTIVE.value:
                raise serializers.ValidationError(_("请先启用网关，然后再启用 MCPServer。"))
            if self.instance.stage.status == StageStatusEnum.INACTIVE.value:
                raise serializers.ValidationError(_("请先发布资源版本到对应环境，然后再启用 MCPServer。"))

        return status


class MCPServerUpdateLabelsInputSLZ(serializers.ModelSerializer):
    labels = serializers.ListField(child=serializers.CharField(), required=True, help_text="MCPServer 标签列表")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateLabelsInputSLZ"
        model = MCPServer
        fields = ("labels",)
        lookup_field = "id"


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
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerToolOutputSLZ"

    def get_labels(self, obj):
        return self.context["labels"].get(obj.id, [])

    def get_tool_name(self, obj) -> str:
        """获取工具名称（重命名后的名称）"""
        tool_name_map = self.context.get("tool_name_map", {})
        return tool_name_map.get(obj.name, "")


class MCPServerGuidelineOutputSLZ(serializers.Serializer):
    content = serializers.CharField(read_only=True, help_text="MCPServer 使用指南")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerGuidelineOutputSLZ"


class MCPServerUserCustomDocInputSLZ(serializers.Serializer):
    content = serializers.CharField(required=True, allow_blank=False, help_text="用户自定义文档内容")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUserCustomDocInputSLZ"


class MCPServerUserCustomDocOutputSLZ(serializers.Serializer):
    content = serializers.CharField(read_only=True, allow_blank=True, help_text="用户自定义文档内容")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUserCustomDocOutputSLZ"


class MCPServerToolDocOutputSLZ(serializers.Serializer):
    type = serializers.CharField(read_only=True, help_text="文档类型")
    content = serializers.CharField(read_only=True, help_text="文档内容")
    updated_time = serializers.DateTimeField(read_only=True, help_text="文档更新时间")
    schema = serializers.DictField(read_only=True, help_text="资源 schema")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerToolDocOutputSLZ"


class MCPServerStageReleaseCheckInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(required=True, help_text="Stage ID")
    resource_version_id = serializers.IntegerField(required=True, help_text="资源版本 ID")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerStageReleaseCheckInputSLZ"


class MCPServerBaseSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 中文名/显示名称")

    def get_title(self, obj) -> str:
        if isinstance(obj, dict):
            return obj.get("title") or obj.get("name", "")
        return obj.title if obj.title else obj.name

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerBaseSLZ"


class MCPServerStageReleaseCheckDetailOutputSLZ(serializers.Serializer):
    resource_name = serializers.CharField(read_only=True, help_text="资源名称")
    mcp_server = MCPServerBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerStageReleaseCheckDetailOutputSLZ"


class MCPServerStageReleaseCheckOutputSLZ(serializers.Serializer):
    has_related_changes = serializers.BooleanField(read_only=True, help_text="是否存在相关变更")
    deleted_resource_count = serializers.IntegerField(read_only=True, help_text="删除的资源数量")
    details = serializers.ListField(
        child=MCPServerStageReleaseCheckDetailOutputSLZ(), read_only=True, help_text="变更详情"
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerStageReleaseCheckOutputSLZ"


class MCPServerAppPermissionListInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=False, help_text="蓝鲸应用 ID")
    grant_type = serializers.ChoiceField(
        choices=MCPServerAppPermissionGrantTypeEnum.get_choices(), required=False, help_text="授权类型"
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionListInputSLZ"


class MCPServerAppPermissionListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    bk_app_code = serializers.CharField(required=True, help_text="蓝鲸应用 ID")
    expires = serializers.DateTimeField(help_text="过期时间")
    grant_type = serializers.ChoiceField(
        choices=MCPServerAppPermissionGrantTypeEnum.get_choices(), help_text="授权类型"
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionListOutputSLZ"


class MCPServerAppPermissionCreateInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=True, validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionCreateInputSLZ"


class MCPServerAppPermissionApplyListInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=False, help_text="蓝鲸应用 ID")
    applied_by = serializers.CharField(required=False, help_text="申请人")
    state = serializers.ChoiceField(
        choices=MCPServerAppPermissionApplyProcessedStateEnum.get_choices(),
        required=True,
        help_text="审批处理状态",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionApplyListInputSLZ"


class MCPServerAppPermissionApplyListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    bk_app_code = serializers.CharField(read_only=True, help_text="蓝鲸应用 ID")
    applied_by = serializers.CharField(read_only=True, help_text="申请人")
    applied_time = serializers.DateTimeField(read_only=True, help_text="申请时间")
    status = serializers.ChoiceField(
        read_only=True, choices=MCPServerAppPermissionApplyStatusEnum.get_choices(), help_text="审批状态"
    )
    mcp_server = MCPServerBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionApplyListOutputSLZ"


class MCPServerAppPermissionApplyUpdateInputSLZ(serializers.ModelSerializer):
    status = serializers.ChoiceField(
        required=True,
        choices=[
            MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            MCPServerAppPermissionApplyStatusEnum.REJECTED.value,
        ],
        help_text="审批状态",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionApplyUpdateInputSLZ"
        model = MCPServerAppPermissionApply
        fields = ("status", "comment")
        lookup_field = "id"


class MCPServerRemotePromptsQueryInputSLZ(serializers.Serializer):
    """查询第三方平台 Prompts 列表的输入序列化器"""

    keyword = serializers.CharField(required=False, allow_blank=True, default="", help_text="搜索关键字")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRemotePromptsQueryInputSLZ"


class MCPServerRemotePromptsOutputSLZ(serializers.Serializer):
    """获取远程 Prompts 列表的输出序列化器"""

    prompts = serializers.ListField(
        child=MCPServerPromptItemSLZ(),
        read_only=True,
        help_text="Prompts 列表",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRemotePromptsOutputSLZ"


class MCPServerRemotePromptsBatchInputSLZ(serializers.Serializer):
    """批量获取第三方平台 Prompts 内容的输入序列化器"""

    ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=True,
        min_length=1,
        help_text="Prompt ID 列表",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRemotePromptsBatchInputSLZ"


class MCPServerRemotePromptsBatchOutputSLZ(serializers.Serializer):
    """批量获取远程 Prompts 内容的输出序列化器"""

    prompts = serializers.ListField(
        child=MCPServerPromptItemSLZ(),
        read_only=True,
        help_text="Prompts 列表（包含内容）",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerRemotePromptsBatchOutputSLZ"
