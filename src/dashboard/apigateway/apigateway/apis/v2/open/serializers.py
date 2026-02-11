# -*- coding: utf-8 -*-
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

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerLeastPrivilegeEnum,
    MCPServerProtocolTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.permission.constants import GrantDimensionEnum, PermissionApplyExpireDaysEnum
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.validators import BKAppCodeValidator
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.service.mcp.mcp_server import (
    build_mcp_server_application_url,
    build_mcp_server_detail_url,
    build_mcp_server_permission_approval_url,
    build_mcp_server_url,
)


class GatewayListInputSLZ(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayListInputSLZ"


class GatewayListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayListOutputSLZ"


class GatewayRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return obj.maintainers

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayRetrieveOutputSLZ"


class GatewayAppPermissionApplyInputSLZ(serializers.Serializer):
    """
    普通应用直接申请访问网关API的权限
    - 提供给普通应用的接口
    - 开源版申请权限，为保障权限有效性，可申请永久有效的权限
    - 暂支持按网关申请，不支持按资源申请
    """

    # target_app_code 与发送请求的应用账号一致，此 app_code 必定已存在，不需要重复校验
    target_app_code = serializers.CharField()
    reason = serializers.CharField(allow_blank=True, required=False, default="")
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        required=False,
    )
    grant_dimension = serializers.ChoiceField(choices=[GrantDimensionEnum.API.value])

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayAppPermissionApplyInputSLZ"

    def validate_target_app_code(self, value):
        request = self.context["request"]
        if request.app.app_code != value:
            raise serializers.ValidationError(
                _("应用【{app_code}】不能为其它应用【{value}】申请访问网关API的权限。").format(
                    app_code=request.app.app_code, value=value
                )
            )

        return value

    def validate(self, data):
        self._validate_allow_apply(data["target_app_code"], data["grant_dimension"])
        return data

    def _validate_allow_apply(self, bk_app_code: str, grant_dimension: str):
        """
        校验是否允许申请权限
        - 已拥有权限，且未过期，不能申请
        - 已存在待审批单据，不能申请
        """
        allow, reason = PermissionDimensionManager.get_manager(grant_dimension).allow_apply_permission(
            self.context["request"].gateway.id,
            bk_app_code,
        )
        if not allow:
            raise serializers.ValidationError(reason)


class GatewayAppPermissionApplyOutputSLZ(serializers.Serializer):
    record_id = serializers.IntegerField(help_text="申请记录ID")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayAppPermissionApplyOutputSLZ"


class MCPServerListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述"
    )

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerListInputSLZ"


class MCPServerBaseSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 中文名/显示名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerBaseSLZ"


class MCPServerPermissionBaseOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    bk_app_code = serializers.CharField(read_only=True, help_text="蓝鲸应用 ID")
    expires = serializers.DateTimeField(read_only=True, help_text="过期时间")
    grant_type = serializers.ChoiceField(
        read_only=True, choices=MCPServerAppPermissionGrantTypeEnum.get_choices(), help_text="授权类型"
    )

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerPermissionBaseOutputSLZ"


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

    oauth2_enabled = serializers.BooleanField(read_only=True, help_text="是否开启 OAuth2 认证")

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")
    gateway = serializers.SerializerMethodField(help_text="MCPServer 网关")

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")
    detail_url = serializers.SerializerMethodField(help_text="MCPServer 网关站点详情 URL")

    updated_by = serializers.CharField(read_only=True, help_text="更新人")
    created_by = serializers.CharField(read_only=True, help_text="创建人")
    updated_time = serializers.DateTimeField(read_only=True, help_text="更新时间")
    created_time = serializers.DateTimeField(read_only=True, help_text="创建时间")

    def get_stage(self, obj) -> Dict[str, Any]:
        return self.context["stages"][obj.stage.id]

    def get_gateway(self, obj) -> Dict[str, Any]:
        return self.context["gateways"][obj.gateway.id]

    def get_url(self, obj) -> str:
        return build_mcp_server_url(obj.name, obj.protocol_type)

    def get_detail_url(self, obj) -> str:
        return build_mcp_server_detail_url(obj.id)

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerBaseOutputSLZ"


class MCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerListOutputSLZ"


class MCPServerAppPermissionListInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=True, validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerAppPermissionListInputSLZ"


class MCPServerAppPermissionListOutputSLZ(MCPServerPermissionBaseOutputSLZ):
    mcp_server = MCPServerBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerAppPermissionListOutputSLZ"


class MCPServerPermissionListOutputSLZ(MCPServerPermissionBaseOutputSLZ):
    mcp_server = MCPServerBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerPermissionListOutputSLZ"


class MCPServerAppPermissionApplyCreateInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=True, validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")
    mcp_server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True,
    )
    applied_by = serializers.CharField(required=True, help_text="申请人")
    reason = serializers.CharField(required=True, help_text="申请原因")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerAppPermissionApplyCreateInputSLZ"


class MCPServerAppPermissionApplyCreateOutputSLZ(serializers.Serializer):
    record_id = serializers.IntegerField(source="id", read_only=True, help_text="申请记录 ID")
    bk_app_code = serializers.CharField(read_only=True, help_text="蓝鲸应用 ID")
    mcp_server_id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    approval_url = serializers.SerializerMethodField(help_text="权限审批 URL")

    def get_approval_url(self, obj) -> str:
        return build_mcp_server_permission_approval_url(obj.mcp_server.gateway_id, obj.mcp_server_id)

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerAppPermissionApplyCreateOutputSLZ"


class MCPServerAppPermissionRecordListInputSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(required=True, validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")
    mcp_server_id = serializers.IntegerField(required=False, allow_null=True, help_text="MCPServer ID")
    record_id = serializers.IntegerField(required=False, allow_null=True, help_text="申请记录 ID")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerAppPermissionRecordListInputSLZ"


class MCPServerAppPermissionApplyRecordListOutputSLZ(serializers.Serializer):
    mcp_server = MCPServerBaseSLZ()
    id = serializers.IntegerField(read_only=True, help_text="申请记录 ID")
    bk_app_code = serializers.CharField(read_only=True, help_text="蓝鲸应用 ID")
    applied_by = serializers.CharField(read_only=True, help_text="申请人")
    applied_time = serializers.DateTimeField(read_only=True, help_text="申请时间")
    handled_by = serializers.CharField(read_only=True, help_text="处理人")
    handled_time = serializers.DateTimeField(read_only=True, help_text="处理时间")
    status = serializers.CharField(read_only=True, help_text="审批状态")
    status_display = serializers.SerializerMethodField(read_only=True)
    comment = serializers.CharField(read_only=True, help_text="备注")
    reason = serializers.CharField(read_only=True, help_text="申请原因")
    expire_days = serializers.IntegerField(read_only=True, help_text="过期天数")
    approval_url = serializers.SerializerMethodField(help_text="权限审批 URL")

    def get_status_display(self, obj):
        return MCPServerAppPermissionApplyStatusEnum.get_choice_label(obj.status)

    def get_approval_url(self, obj) -> str:
        return build_mcp_server_permission_approval_url(obj.mcp_server.gateway_id, obj.mcp_server_id)

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.MCPServerAppPermissionApplyRecordListOutputSLZ"


class UserMCPServerListInputSLZ(serializers.Serializer):
    is_public = serializers.BooleanField(
        required=False,
        allow_null=True,
        help_text="是否公开，true：公开，false：不公开，不传或传空则查询全部",
    )
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述"
    )

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.UserMCPServerListInputSLZ"


class UserMCPServerListOutputSLZ(MCPServerBaseOutputSLZ):
    application_url = serializers.SerializerMethodField(help_text="应用态 URL")
    least_privilege = serializers.SerializerMethodField(help_text="最低权限")

    def get_application_url(self, obj) -> str:
        least_privilege = self.context["least_privileges"].get((obj.gateway.id, obj.stage.id))
        if least_privilege == MCPServerLeastPrivilegeEnum.APPLICATION.value:
            return build_mcp_server_application_url(obj.name, obj.protocol_type)
        return ""

    def get_least_privilege(self, obj) -> str:
        return self.context["least_privileges"].get((obj.gateway.id, obj.stage.id), "")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.UserMCPServerListOutputSLZ"


class AuthConfigOutputSLZ(serializers.Serializer):
    """认证配置输出"""

    user_verified_required = serializers.BooleanField(read_only=True, help_text="是否需要用户认证")
    app_verified_required = serializers.BooleanField(read_only=True, help_text="是否需要应用认证")
    resource_perm_required = serializers.BooleanField(read_only=True, help_text="是否需要资源权限")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.AuthConfigOutputSLZ"


class GatewayResourceListOutputSLZ(serializers.Serializer):
    """网关资源列表输出"""

    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    description = SerializerTranslatedField(
        default_field="description_i18n", translated_fields={"en": "description_en"}
    )
    method = serializers.CharField(read_only=True, help_text="请求方法")
    path = serializers.SerializerMethodField(help_text="资源路径")
    match_subpath = serializers.BooleanField(read_only=True, help_text="是否匹配子路径")
    enable_websocket = serializers.BooleanField(read_only=True, help_text="是否启用 WebSocket")
    is_public = serializers.BooleanField(read_only=True, help_text="是否公开")
    labels = serializers.SerializerMethodField(help_text="标签列表")
    auth_config = serializers.SerializerMethodField(help_text="认证配置")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayResourceListOutputSLZ"

    def get_path(self, obj):
        """返回路径显示，包含子路径匹配标识"""
        return obj.path_display

    def get_labels(self, obj):
        """获取标签列表"""
        return self.context.get("labels", {}).get(obj.id, [])

    def get_auth_config(self, obj):
        """获取认证配置"""
        auth_config = self.context.get("auth_configs", {}).get(obj.id, {})
        return AuthConfigOutputSLZ(
            {
                "user_verified_required": auth_config.get("auth_verified_required", False),
                "app_verified_required": auth_config.get("app_verified_required", True),
                "resource_perm_required": auth_config.get("resource_perm_required", False),
            }
        ).data


class GatewayResourceDetailInputSLZ(serializers.Serializer):
    """网关资源详情查询参数"""

    stage_name = serializers.CharField(required=True, help_text="网关环境名称")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayResourceDetailInputSLZ"


class GatewayResourceDetailOutputSLZ(serializers.Serializer):
    """网关资源详情输出"""

    id = serializers.IntegerField(read_only=True, help_text="资源 ID")
    name = serializers.CharField(read_only=True, help_text="资源名称")
    description = SerializerTranslatedField(
        default_field="description_i18n",
        translated_fields={"en": "description_en"},
        read_only=True,
        help_text="资源描述",
    )
    method = serializers.CharField(read_only=True, help_text="请求方法")
    path = serializers.CharField(read_only=True, help_text="资源路径")
    match_subpath = serializers.BooleanField(read_only=True, help_text="是否匹配子路径")
    enable_websocket = serializers.BooleanField(read_only=True, help_text="是否启用 WebSocket")
    is_public = serializers.BooleanField(read_only=True, help_text="是否公开")
    schema = serializers.DictField(read_only=True, help_text="资源的 OpenAPI Schema 定义")
    doc = serializers.DictField(read_only=True, help_text="资源文档信息", allow_null=True)
    auth_config = AuthConfigOutputSLZ(read_only=True, help_text="认证配置")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GatewayResourceDetailOutputSLZ"


class GetDatetimeInputSLZ(serializers.Serializer):
    tz_name = serializers.CharField(required=False, allow_blank=True, help_text="时区名，默认 Asia/Shanghai")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GetDatetimeInputSLZ"


class GetDatetimeOutputSLZ(serializers.Serializer):
    datetime = serializers.CharField(read_only=True, help_text="当前时间")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GetDatetimeOutputSLZ"


class GetCurrentUnixTimestampOutputSLZ(serializers.Serializer):
    unix_timestamp = serializers.IntegerField(read_only=True, help_text="当前时间戳")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.GetCurrentUnixTimestampOutputSLZ"


class ParseDatetimeStrToTimestampInputSLZ(serializers.Serializer):
    datetime = serializers.CharField(required=True, help_text="时间字符串")
    datetime_format = serializers.CharField(
        required=False, allow_blank=True, help_text="时间格式，默认 %Y-%m-%d %H:%M:%S, python's datetime format"
    )

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.ParseDatetimeStrToTimestampInputSLZ"


class ParseDatetimeStrToTimestampOutputSLZ(serializers.Serializer):
    timestamp = serializers.IntegerField(read_only=True, help_text="时间戳")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.ParseDatetimeStrToTimestampOutputSLZ"


class LogSearchByRequestIdInputSLZ(serializers.Serializer):
    request_id = serializers.CharField(required=True, help_text="请求 ID")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.LogSearchByRequestIdInputSLZ"


class LogSearchByRequestIdOutputSLZ(serializers.Serializer):
    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求 ID")
    timestamp = serializers.IntegerField(required=False, allow_null=True, help_text="请求时间戳")

    stage = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="环境")
    resource_id = serializers.IntegerField(required=False, allow_null=True, help_text="资源 ID")
    resource_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="资源名称")

    app_code = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="应用编码")
    client_ip = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="客户端 IP")
    method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求方法")
    http_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求域名")
    http_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求路径")
    params = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求参数")
    body = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求体")

    backend_scheme = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求协议")
    backend_method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求方法")
    backend_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求域名")
    backend_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="后端请求路径")
    response_body = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="响应体")
    status = serializers.IntegerField(required=False, allow_null=True, help_text="响应状态码")

    request_duration = serializers.IntegerField(required=False, allow_null=True, help_text="请求耗时")
    backend_duration = serializers.IntegerField(required=False, allow_null=True, help_text="后端请求耗时")

    code_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="状态码名称")
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="错误")
    response_desc = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="响应描述")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.LogSearchByRequestIdOutputSLZ"


class OAuthProtectedResourceInputSLZ(serializers.Serializer):
    resource = serializers.URLField(required=True, allow_blank=False, help_text="The resource URL")

    class Meta:
        ref_name = "apigateway.apis.v2.open.serializers.OAuthProtectedResourceInputSLZ"
