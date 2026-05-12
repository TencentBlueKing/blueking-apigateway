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

from rest_framework import serializers

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import (
    GrantDimensionEnum,
    PermissionApplyExpireDaysEnum,
)
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper

# ========== 查询输入序列化器 ==========


class WorkbenchGatewayPermissionQueryInputSLZ(serializers.Serializer):
    """个人工作台 - API 网关权限查询输入"""

    bk_app_code = serializers.CharField(required=False, allow_blank=True, help_text="蓝鲸应用 ID")
    applied_by = serializers.CharField(required=False, allow_blank=True, help_text="申请人")
    grant_dimension = serializers.ChoiceField(
        choices=GrantDimensionEnum.get_choices(), required=False, help_text="授权维度"
    )
    keyword = serializers.CharField(
        required=False, allow_blank=True, help_text="搜索关键字（模糊匹配网关名称或应用ID）"
    )

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchGatewayPermissionQueryInputSLZ"


class WorkbenchMCPPermissionQueryInputSLZ(serializers.Serializer):
    """个人工作台 - MCP Server 权限查询输入"""

    bk_app_code = serializers.CharField(required=False, allow_blank=True, help_text="蓝鲸应用 ID")
    applied_by = serializers.CharField(required=False, allow_blank=True, help_text="申请人")
    keyword = serializers.CharField(
        required=False, allow_blank=True, help_text="搜索关键字（模糊匹配 MCP Server 名称或应用ID）"
    )

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchMCPPermissionQueryInputSLZ"


# ========== API 网关 输出序列化器 ==========


class WorkbenchGatewayPermissionApplyOutputSLZ(serializers.ModelSerializer):
    """个人工作台 - API 网关代办/我的申请 输出序列化器"""

    gateway_name = serializers.SerializerMethodField(help_text="网关名称")
    expire_days_display = serializers.SerializerMethodField(help_text="权限期限显示")
    grant_dimension_display = serializers.SerializerMethodField(help_text="授权维度显示")
    itsm_ticket_url = serializers.SerializerMethodField(help_text="ITSM 单据中心链接")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchGatewayPermissionApplyOutputSLZ"
        model = AppPermissionApply
        fields = [
            "id",
            "bk_app_code",
            "gateway_name",
            "grant_dimension",
            "grant_dimension_display",
            "expire_days",
            "expire_days_display",
            "reason",
            "applied_by",
            "created_time",
            "status",
            "itsm_ticket_id",
            "itsm_ticket_url",
        ]
        read_only_fields = fields

    def get_gateway_name(self, obj) -> str:
        return obj.gateway.name if obj.gateway else ""

    def get_expire_days_display(self, obj) -> str:
        return PermissionApplyExpireDaysEnum.get_choice_label(obj.expire_days)

    def get_grant_dimension_display(self, obj) -> str:
        return GrantDimensionEnum.get_choice_label(obj.grant_dimension)

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)


class WorkbenchGatewayPermissionRecordOutputSLZ(serializers.ModelSerializer):
    """个人工作台 - API 网关已办 输出序列化器"""

    gateway_name = serializers.SerializerMethodField(help_text="网关名称")
    expire_days_display = serializers.SerializerMethodField(help_text="权限期限显示")
    grant_dimension_display = serializers.SerializerMethodField(help_text="授权维度显示")
    itsm_ticket_url = serializers.SerializerMethodField(help_text="ITSM 单据中心链接")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchGatewayPermissionRecordOutputSLZ"
        model = AppPermissionRecord
        fields = [
            "id",
            "bk_app_code",
            "gateway_name",
            "grant_dimension",
            "grant_dimension_display",
            "expire_days",
            "expire_days_display",
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
        return obj.gateway.name if obj.gateway else ""

    def get_expire_days_display(self, obj) -> str:
        return PermissionApplyExpireDaysEnum.get_choice_label(obj.expire_days)

    def get_grant_dimension_display(self, obj) -> str:
        return GrantDimensionEnum.get_choice_label(obj.grant_dimension)

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)


# ========== MCP Server 输出序列化器 ==========


class WorkbenchMCPServerBaseSLZ(serializers.Serializer):
    """MCP Server 简要信息"""

    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 显示名称")

    class Meta:
        ref_name = "apigateway.apis.web.personal_workbench.serializers.WorkbenchMCPServerBaseSLZ"

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name


class WorkbenchMCPPermissionApplyOutputSLZ(serializers.ModelSerializer):
    """个人工作台 - MCP Server 代办/我的申请 输出序列化器"""

    mcp_server = WorkbenchMCPServerBaseSLZ(help_text="MCP Server 信息")
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
            "applied_time",
            "reason",
            "expire_days",
            "status",
            "status_display",
            "itsm_ticket_id",
            "itsm_ticket_url",
        ]
        read_only_fields = fields

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)

    def get_status_display(self, obj) -> str:
        return MCPServerAppPermissionApplyStatusEnum.get_choice_label(obj.status)


class WorkbenchMCPPermissionHandledOutputSLZ(serializers.ModelSerializer):
    """个人工作台 - MCP Server 已办 输出序列化器"""

    mcp_server = WorkbenchMCPServerBaseSLZ(help_text="MCP Server 信息")
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

    def get_itsm_ticket_url(self, obj) -> str:
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)

    def get_status_display(self, obj) -> str:
        return MCPServerAppPermissionApplyStatusEnum.get_choice_label(obj.status)
