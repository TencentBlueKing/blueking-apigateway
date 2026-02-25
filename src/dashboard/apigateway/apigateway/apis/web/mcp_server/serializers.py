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
    FEATURED_MCP_CATEGORY_NAME,
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerAppPermissionApplyProcessedStateEnum,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermissionApply,
    MCPServerCategory,
)
from apigateway.biz.mcp_server.prompt import MCPServerPromptHandler
from apigateway.biz.permission.permission import ResourcePermissionHandler
from apigateway.biz.validators import BKAppCodeValidator, MCPServerHandler, MCPServerValidator
from apigateway.common.constants import LanguageCodeEnum
from apigateway.common.django.translation import get_current_language_code
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.service.mcp.mcp_server import build_mcp_server_url

logger = logging.getLogger(__name__)


class MCPServerCategoryOutputSLZ(serializers.Serializer):
    """MCPServer 分类输出序列化器"""

    id = serializers.IntegerField(read_only=True, help_text="分类 ID")
    name = serializers.CharField(read_only=True, help_text="分类名称（英文标识）")
    display_name = serializers.SerializerMethodField(help_text="分类显示名称（根据语言环境返回）")
    description = serializers.CharField(read_only=True, help_text="分类描述")
    sort_order = serializers.IntegerField(read_only=True, help_text="排序顺序")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerCategoryOutputSLZ"

    def get_display_name(self, obj) -> str:
        """根据当前语言环境返回分类名称：英文环境返回 name，中文环境返回 display_name"""
        language_code = get_current_language_code()
        # 英文环境返回 name，否则返回 display_name
        if language_code == LanguageCodeEnum.EN.value:
            return obj.name
        return obj.display_name


class MCPServerListInputSLZ(serializers.Serializer):
    """MCPServer 列表查询输入序列化器"""

    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述"
    )
    status = serializers.ChoiceField(
        choices=MCPServerStatusEnum.get_choices(),
        required=False,
        help_text="MCPServer 状态筛选",
    )
    stage_id = serializers.IntegerField(
        required=False,
        help_text="环境 ID 筛选",
    )
    label = serializers.CharField(allow_blank=True, required=False, help_text="标签筛选")
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
            ("-status", "按状态排序（启用优先）"),
        ],
        default="-status,-updated_time",
        required=False,
        help_text="排序方式",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerListInputSLZ"

    def validate_categories(self, value):
        """解析分类参数，支持多个分类名称（逗号分隔）"""
        if not value:
            return []
        # 解析逗号分隔的分类名称，去除空白
        return [cat.strip() for cat in value.split(",") if cat.strip()]


def validate_category_ids_common(category_ids: List[int]) -> List[int]:
    """
    通用的分类 ID 验证逻辑，检查分类是否存在且启用。

    Args:
        category_ids: 分类 ID 列表

    Returns:
        验证通过的分类 ID 列表

    Raises:
        serializers.ValidationError: 如果存在无效的分类 ID
    """
    if not category_ids:
        return category_ids

    # 检查分类是否存在且启用
    valid_categories = MCPServerCategory.objects.filter(id__in=category_ids, is_active=True)
    valid_category_ids = set(valid_categories.values_list("id", flat=True))

    invalid_ids = set(category_ids) - valid_category_ids
    if invalid_ids:
        raise serializers.ValidationError(
            _("分类 ID 列表中包含无效的分类：{}").format(", ".join(map(str, invalid_ids)))
        )

    return category_ids


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


class MCPServerCreateInputSLZ(serializers.ModelSerializer):
    stage_id = serializers.IntegerField(help_text="Stage ID")
    labels = serializers.ListField(child=serializers.CharField(), required=False, help_text="MCPServer 标签列表")
    resource_names = serializers.ListField(
        child=serializers.CharField(), required=True, help_text="MCPServer 资源名称列表"
    )
    tool_names = serializers.ListField(
        child=serializers.CharField(),
        required=True,
        help_text="MCPServer 工具名称列表，默认等于 resource_names，如果有设置别名，替换对应值",
    )
    name = serializers.CharField(required=True, help_text="MCPServer 名称", max_length=64)
    title = serializers.CharField(
        required=False, allow_blank=True, help_text="MCPServer 中文名/显示名称", max_length=128
    )
    description = serializers.CharField(required=True, allow_blank=False, help_text="MCPServer 描述")
    prompts = serializers.ListField(
        child=MCPServerPromptItemSLZ(), required=False, default=list, help_text="Prompts 列表"
    )
    protocol_type = serializers.ChoiceField(
        choices=MCPServerProtocolTypeEnum.get_choices(),
        required=False,
        default=MCPServerProtocolTypeEnum.SSE.value,
        help_text="MCPServer 协议类型",
    )
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        default=list,
        help_text="MCPServer 分类 ID 列表",
    )
    oauth2_public_client_enabled = serializers.BooleanField(
        required=False,
        default=False,
        help_text="是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权",
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
            "tool_names",
            "prompts",
            "protocol_type",
            "category_ids",
            "oauth2_public_client_enabled",
        )
        lookup_field = "id"
        validators = [MCPServerValidator()]

    def validate_resource_names(self, resource_names):
        """验证资源名称列表"""
        if not resource_names:
            raise serializers.ValidationError(_("资源名称列表不能为空"))
        valid_resource_names = self.context["valid_resource_names"]

        if len(resource_names) != len(set(resource_names)):
            raise serializers.ValidationError(_("资源名称列表中不能存在重复的资源名称"))

        for resource_name in resource_names:
            if resource_name not in valid_resource_names:
                raise serializers.ValidationError(
                    _("资源名称列表非法，请检查当前环境发布的最新版本中对应资源名称是否存在")
                    + f"resource_name={resource_name}"
                )
        return resource_names

    def validate_tool_names(self, tool_names):
        """验证工具名称列表"""
        if len(tool_names) == 0:
            raise serializers.ValidationError(_("工具名称列表不能为空"))

        if len(tool_names) != len(set(tool_names)):
            raise serializers.ValidationError(_("工具名称不能重复"))

        if len(tool_names) != len(self.initial_data["resource_names"]):
            raise serializers.ValidationError(_("工具名称列表长度与资源名称列表长度不一致"))

        return tool_names

    def validate_category_ids(self, category_ids):
        """验证分类 ID 列表"""
        return validate_category_ids_common(category_ids)

    def create(self, validated_data):
        prompts = validated_data.pop("prompts", [])
        resource_names = validated_data.pop("resource_names")
        tool_names = validated_data.pop("tool_names")
        category_ids = validated_data.pop("category_ids", [])

        validated_data["gateway_id"] = self.context["gateway"].id
        validated_data["created_by"] = self.context["created_by"]
        validated_data["status"] = self.context["status"]

        # 创建实例并设置资源名称，一次性保存
        instance = MCPServer(**validated_data)
        instance.update_resource_names(resource_names, tool_names)
        instance.save()

        # 设置分类
        if category_ids:
            categories = MCPServerCategory.objects.filter(id__in=category_ids, is_active=True)
            instance.categories.set(categories)

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
    resource_names = serializers.ListField(
        child=serializers.CharField(), read_only=True, help_text="MCPServer 资源名称列表"
    )
    tool_names = serializers.ListField(
        child=serializers.CharField(), read_only=True, help_text="MCPServer 工具名称列表"
    )

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")

    status = serializers.ChoiceField(
        read_only=True, help_text="MCPServer 状态", choices=MCPServerStatusEnum.get_choices()
    )

    protocol_type = serializers.ChoiceField(
        read_only=True, help_text="MCP 协议类型", choices=MCPServerProtocolTypeEnum.get_choices()
    )

    oauth2_public_client_enabled = serializers.BooleanField(
        read_only=True, help_text="是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权"
    )

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")

    updated_time = serializers.DateTimeField(read_only=True, help_text="MCPServer 更新时间")
    created_time = serializers.DateTimeField(read_only=True, help_text="MCPServer 创建时间")

    # 分类信息
    categories = serializers.SerializerMethodField(help_text="MCPServer 分类列表")
    is_official = serializers.SerializerMethodField(help_text="是否为官方")
    is_featured = serializers.SerializerMethodField(help_text="是否为精选")

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerBaseOutputSLZ"

    def get_stage(self, obj) -> Dict[str, Any]:
        return self.context["stages"][obj.stage.id]

    def get_url(self, obj) -> str:
        return build_mcp_server_url(obj.name, obj.protocol_type)

    def get_categories(self, obj):
        """获取分类信息，利用预加载的数据避免 N+1 查询"""
        # 使用预取的 categories 关系数据
        categories = obj.categories.all()
        # 在内存中过滤和排序
        active_categories = sorted(
            (cat for cat in categories if cat.is_active),
            key=lambda cat: cat.sort_order,
        )
        return MCPServerCategoryOutputSLZ(active_categories, many=True).data

    def get_is_official(self, obj) -> bool:
        """是否为官方，利用预加载的数据避免 N+1 查询"""
        categories = obj.categories.all()
        return any(cat.name == OFFICIAL_MCP_CATEGORY_NAME and cat.is_active for cat in categories)

    def get_is_featured(self, obj) -> bool:
        """是否为精选，利用预加载的数据避免 N+1 查询"""
        categories = obj.categories.all()
        return any(cat.name == FEATURED_MCP_CATEGORY_NAME and cat.is_active for cat in categories)


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
        child=serializers.CharField(), required=False, help_text="MCPServer 资源名称列表"
    )
    tool_names = serializers.ListField(
        child=serializers.CharField(), required=False, help_text="MCPServer 工具名称列表"
    )
    title = serializers.CharField(
        required=False, allow_blank=True, help_text="MCPServer 中文名/显示名称", max_length=128
    )
    description = serializers.CharField(required=True, allow_blank=False, help_text="MCPServer 描述")
    prompts = serializers.ListField(child=MCPServerPromptItemSLZ(), required=False, help_text="Prompts 列表")
    protocol_type = serializers.ChoiceField(
        choices=MCPServerProtocolTypeEnum.get_choices(),
        required=False,
        help_text="MCP 协议类型",
    )
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="MCPServer 分类 ID 列表",
    )
    oauth2_public_client_enabled = serializers.BooleanField(
        required=False,
        help_text="是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权",
    )

    def validate_resource_names(self, resource_names):
        """验证资源名称列表"""
        if not resource_names:
            raise serializers.ValidationError(_("资源名称列表不能为空"))
        valid_resource_names = self.context["valid_resource_names"]

        if len(resource_names) != len(set(resource_names)):
            raise serializers.ValidationError(_("资源名称列表中不能存在重复的资源名称"))

        for resource_name in resource_names:
            if resource_name not in valid_resource_names:
                raise serializers.ValidationError(
                    _("资源名称列表非法，请检查当前环境发布的最新版本中对应资源名称是否存在")
                    + f"resource_name={resource_name}"
                )
        return resource_names

    def validate_tool_names(self, tool_names):
        """验证工具名称列表"""
        if len(tool_names) == 0:
            raise serializers.ValidationError(_("工具名称列表不能为空"))

        if len(tool_names) != len(set(tool_names)):
            raise serializers.ValidationError(_("工具名称不能重复"))

        if len(tool_names) != len(self.initial_data["resource_names"]):
            raise serializers.ValidationError(_("工具名称列表长度与资源名称列表长度不一致"))

        return tool_names

    def validate_category_ids(self, category_ids):
        """验证分类 ID 列表"""
        return validate_category_ids_common(category_ids)

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerUpdateInputSLZ"
        model = MCPServer
        fields = (
            "title",
            "description",
            "is_public",
            "labels",
            "resource_names",
            "tool_names",
            "prompts",
            "protocol_type",
            "category_ids",
            "oauth2_public_client_enabled",
        )
        lookup_field = "id"

    def update(self, instance, validated_data):
        prompts = validated_data.pop("prompts", None)
        category_ids = validated_data.pop("category_ids", None)

        resource_names = validated_data.pop("resource_names", None)
        tool_names = validated_data.pop("tool_names", None)

        # 更新普通字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # 如果传入了 resource_names，使用 model 层方法更新
        if resource_names is not None:
            if tool_names is None:
                raise serializers.ValidationError(_("工具名称列表不能为空"))

            if len(tool_names) != len(resource_names):
                raise serializers.ValidationError(_("工具名称列表长度与资源名称列表长度不一致"))

            instance.update_resource_names(resource_names, tool_names)

        # 一次性保存所有更改
        instance.save()

        # 更新分类
        if category_ids is not None:
            if category_ids:
                categories = MCPServerCategory.objects.filter(id__in=category_ids, is_active=True)
                instance.categories.set(categories)
            else:
                instance.categories.clear()

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
    mcp_server_id = serializers.IntegerField(required=False, help_text="MCPServer ID，不传则查询所有")
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
    applied_by = serializers.SerializerMethodField(help_text="申请人")
    applied_time = serializers.DateTimeField(read_only=True, help_text="申请时间")
    status = serializers.ChoiceField(
        read_only=True, choices=MCPServerAppPermissionApplyStatusEnum.get_choices(), help_text="审批状态"
    )
    mcp_server = MCPServerBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerAppPermissionApplyListOutputSLZ"

    def get_applied_by(self, obj):
        return ResourcePermissionHandler.convert_applied_by_to_display_name(
            obj.bk_app_code,
            obj.applied_by,
            self.context.get("gateway_tenant_mode"),
            self.context.get("gateway_tenant_id"),
        )


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


class MCPServerFilterOptionsOutputSLZ(serializers.Serializer):
    """MCPServer 搜索过滤选项输出序列化器，用于前端下拉列表"""

    stages = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="可用的环境列表",
    )
    labels = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="所有可用的标签列表",
    )
    categories = serializers.ListField(
        child=serializers.DictField(),
        read_only=True,
        help_text="可用的分类列表",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerFilterOptionsOutputSLZ"


class MCPServerConfigItemOutputSLZ(serializers.Serializer):
    """MCPServer 单个配置项输出序列化器"""

    name = serializers.CharField(read_only=True, help_text="配置名称（如 cursor, codebuddy, claude, aidev）")
    display_name = serializers.CharField(read_only=True, help_text="配置显示名称")
    content = serializers.CharField(read_only=True, help_text="配置内容（markdown 格式）")
    install_url = serializers.CharField(
        read_only=True, allow_blank=True, required=False, help_text="一键配置 URL（如果支持）"
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerConfigItemOutputSLZ"


class MCPServerConfigListOutputSLZ(serializers.Serializer):
    """MCPServer 配置列表输出序列化器"""

    configs = serializers.ListField(
        child=MCPServerConfigItemOutputSLZ(),
        read_only=True,
        help_text="配置列表",
    )

    class Meta:
        ref_name = "apigateway.apis.web.mcp_server.serializers.MCPServerConfigListOutputSLZ"
