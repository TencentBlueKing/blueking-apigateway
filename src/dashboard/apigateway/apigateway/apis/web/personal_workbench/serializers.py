#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from typing import Any

from rest_framework import serializers

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermissionApply
from apigateway.apps.permission.constants import (
    GrantDimensionEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.core.models import Gateway, Resource
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper

from .constants import WorkbenchFilterTypeEnum

# ========== 下拉筛选项序列化器 ==========


class WorkbenchFilterOptionQueryInputSLZ(serializers.Serializer):
    """个人工作台 - 下拉筛选选项查询输入"""

    type = serializers.ChoiceField(
        choices=WorkbenchFilterTypeEnum.get_choices(),
        default=WorkbenchFilterTypeEnum.PENDING.value,
        help_text="数据来源类型：pending（我的待办）、applied（我的申请）、handled（我的已办）",
    )

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchFilterOptionQueryInputSLZ"


class WorkbenchGatewayFilterOptionSLZ(serializers.ModelSerializer):
    """个人工作台 - 网关下拉筛选项"""

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchGatewayFilterOptionSLZ"
        model = Gateway
        fields = ["id", "name"]
        read_only_fields = fields


class WorkbenchMCPServerFilterOptionSLZ(serializers.ModelSerializer):
    """个人工作台 - MCP Server 下拉筛选项

    输出字段说明：
    - id: MCP Server 唯一标识
    - name: MCP Server 内部名称（唯一标识，用于系统间交互）
    - title: MCP Server 展示名称（为空时回退到 name）
    - gateway_id: 所属网关 ID
    - gateway_name: 所属网关名称
    """

    title = serializers.SerializerMethodField(help_text="MCP Server 展示名称（为空时回退到 name）")
    gateway_name = serializers.SerializerMethodField(help_text="所属网关名称")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchMCPServerFilterOptionSLZ"
        model = MCPServer
        fields = ["id", "name", "title", "gateway_id", "gateway_name"]
        read_only_fields = fields

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    def get_gateway_name(self, obj) -> str:
        return obj.gateway.name


# ========== API 网关 输出序列化器 ==========


class ResourceDetailMixin:
    """资源详情 Mixin，提供 get_resources 方法

    使用方式：View 层通过 serializer context 传入 prefetched_resources（批量预取的资源映射），
    避免 N+1 查询问题。若 context 中无预取数据，则回退到单条查询。
    """

    context: dict[str, Any]

    def get_resources(self, obj) -> list:
        if obj.grant_dimension != GrantDimensionEnum.RESOURCE.value:
            return []
        resource_ids = obj.resource_ids
        if not resource_ids:
            return []

        # 优先使用 View 层预取的资源数据
        prefetched = self.context.get("prefetched_resources")
        if prefetched is not None:
            return [prefetched[rid] for rid in sorted(resource_ids) if rid in prefetched]

        return list(Resource.objects.filter(id__in=resource_ids).values("id", "name", "path", "method").order_by("id"))


class WorkbenchGatewayPermissionApplyOutputSLZ(ResourceDetailMixin, serializers.ModelSerializer):
    """个人工作台 - API 网关待办/我的申请 输出序列化器"""

    gateway_id = serializers.IntegerField(read_only=True, help_text="网关 ID")
    gateway_name = serializers.SerializerMethodField(help_text="网关名称")
    expire_days_display = serializers.SerializerMethodField(help_text="权限期限显示")
    grant_dimension_display = serializers.SerializerMethodField(help_text="授权维度显示")
    applied_by = serializers.SerializerMethodField(help_text="申请人")
    approvers = serializers.SerializerMethodField(help_text="当前网关管理员列表（潜在审批人，非历史实际审批人）")
    itsm_ticket_url = serializers.SerializerMethodField(help_text="ITSM 单据中心链接")
    resources = serializers.SerializerMethodField(help_text="资源维度时的资源列表")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchGatewayPermissionApplyOutputSLZ"
        model = AppPermissionApply
        fields = [
            "id",
            "bk_app_code",
            "gateway_id",
            "gateway_name",
            "grant_dimension",
            "grant_dimension_display",
            "expire_days",
            "expire_days_display",
            "resources",
            "reason",
            "applied_by",
            "approvers",
            "created_time",
            "status",
            "itsm_ticket_id",
            "itsm_ticket_url",
        ]
        read_only_fields = fields

    def get_gateway_name(self, obj) -> str:
        return obj.gateway.name

    def get_expire_days_display(self, obj) -> str:
        return PermissionApplyExpireDaysEnum.get_choice_label(obj.expire_days)

    def get_grant_dimension_display(self, obj) -> str:
        return GrantDimensionEnum.get_choice_label(obj.grant_dimension)

    def get_applied_by(self, obj) -> str:
        return ResourcePermissionHandler.convert_applied_by_to_display_name(
            obj.bk_app_code,
            obj.applied_by,
            obj.gateway.tenant_mode,
            obj.gateway.tenant_id,
        )

    def get_approvers(self, obj) -> list[str]:
        return obj.gateway.maintainers

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)


class WorkbenchGatewayPermissionRecordOutputSLZ(ResourceDetailMixin, serializers.ModelSerializer):
    """个人工作台 - API 网关已办 输出序列化器"""

    gateway_id = serializers.IntegerField(read_only=True, help_text="网关 ID")
    gateway_name = serializers.SerializerMethodField(help_text="网关名称")
    expire_days_display = serializers.SerializerMethodField(help_text="权限期限显示")
    grant_dimension_display = serializers.SerializerMethodField(help_text="授权维度显示")
    applied_by = serializers.SerializerMethodField(help_text="申请人")
    itsm_ticket_url = serializers.SerializerMethodField(help_text="ITSM 单据中心链接")
    resources = serializers.SerializerMethodField(help_text="资源维度时的资源列表")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchGatewayPermissionRecordOutputSLZ"
        model = AppPermissionRecord
        fields = [
            "id",
            "bk_app_code",
            "gateway_id",
            "gateway_name",
            "grant_dimension",
            "grant_dimension_display",
            "expire_days",
            "expire_days_display",
            "resources",
            "reason",
            "applied_by",
            "applied_time",
            "handled_by",
            "handled_time",
            "status",
            "comment",
            "itsm_ticket_id",
            "itsm_ticket_url",
        ]
        read_only_fields = fields

    def get_gateway_name(self, obj) -> str:
        return obj.gateway.name

    def get_expire_days_display(self, obj) -> str:
        return PermissionApplyExpireDaysEnum.get_choice_label(obj.expire_days)

    def get_grant_dimension_display(self, obj) -> str:
        return GrantDimensionEnum.get_choice_label(obj.grant_dimension)

    def get_applied_by(self, obj) -> str:
        return ResourcePermissionHandler.convert_applied_by_to_display_name(
            obj.bk_app_code,
            obj.applied_by,
            obj.gateway.tenant_mode,
            obj.gateway.tenant_id,
        )

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)


# ========== MCP Server 输出序列化器 ==========


class WorkbenchMCPServerBaseSLZ(serializers.Serializer):
    """MCP Server 简要信息"""

    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 显示名称")
    gateway_id = serializers.IntegerField(read_only=True, help_text="所属网关 ID")
    gateway_name = serializers.SerializerMethodField(help_text="所属网关名称")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchMCPServerBaseSLZ"

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    def get_gateway_name(self, obj) -> str:
        return obj.gateway.name


class WorkbenchMCPPermissionApplyOutputSLZ(serializers.ModelSerializer):
    """个人工作台 - MCP Server 待办/我的申请 输出序列化器"""

    mcp_server = WorkbenchMCPServerBaseSLZ(help_text="MCP Server 信息")
    applied_by = serializers.SerializerMethodField(help_text="申请人")
    approvers = serializers.SerializerMethodField(help_text="当前网关管理员列表（潜在审批人，非历史实际审批人）")
    itsm_ticket_url = serializers.SerializerMethodField(help_text="ITSM 单据中心链接")
    status_display = serializers.SerializerMethodField(help_text="审批状态显示")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchMCPPermissionApplyOutputSLZ"
        model = MCPServerAppPermissionApply
        fields = [
            "id",
            "bk_app_code",
            "mcp_server",
            "applied_by",
            "approvers",
            "applied_time",
            "reason",
            "expire_days",
            "status",
            "status_display",
            "itsm_ticket_id",
            "itsm_ticket_url",
        ]
        read_only_fields = fields

    def get_applied_by(self, obj) -> str:
        gateway = obj.mcp_server.gateway
        return ResourcePermissionHandler.convert_applied_by_to_display_name(
            obj.bk_app_code,
            obj.applied_by,
            gateway.tenant_mode,
            gateway.tenant_id,
        )

    def get_approvers(self, obj) -> list[str]:
        return obj.mcp_server.gateway.maintainers

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)

    def get_status_display(self, obj) -> str:
        return MCPServerAppPermissionApplyStatusEnum.get_choice_label(obj.status)


class WorkbenchMCPPermissionHandledOutputSLZ(serializers.ModelSerializer):
    """个人工作台 - MCP Server 已办 输出序列化器"""

    mcp_server = WorkbenchMCPServerBaseSLZ(help_text="MCP Server 信息")
    applied_by = serializers.SerializerMethodField(help_text="申请人")
    itsm_ticket_url = serializers.SerializerMethodField(help_text="ITSM 单据中心链接")
    status_display = serializers.SerializerMethodField(help_text="审批状态显示")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchMCPPermissionHandledOutputSLZ"
        model = MCPServerAppPermissionApply
        fields = [
            "id",
            "bk_app_code",
            "mcp_server",
            "applied_by",
            "applied_time",
            "reason",
            "expire_days",
            "handled_by",
            "handled_time",
            "status",
            "status_display",
            "comment",
            "itsm_ticket_id",
            "itsm_ticket_url",
        ]
        read_only_fields = fields

    def get_applied_by(self, obj) -> str:
        gateway = obj.mcp_server.gateway
        return ResourcePermissionHandler.convert_applied_by_to_display_name(
            obj.bk_app_code,
            obj.applied_by,
            gateway.tenant_mode,
            gateway.tenant_id,
        )

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)

    def get_status_display(self, obj) -> str:
        return MCPServerAppPermissionApplyStatusEnum.get_choice_label(obj.status)
