# -*- coding: utf-8 -*-
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
import logging
import math
from typing import Dict, List

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.mcp_server.constants import (
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerProtocolTypeEnum,
)
from apigateway.apps.monitor.constants import AlarmStatusEnum
from apigateway.apps.permission.constants import (
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    FormattedGrantDimensionEnum,
    GrantDimensionEnum,
    PermissionActionEnum,
    PermissionApplyExpireDaysEnum,
    PermissionStatusEnum,
)
from apigateway.apps.permission.models import AppPermissionRecord
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.biz.permission import ResourcePermissionHandler
from apigateway.biz.validators import BKAppCodeValidator
from apigateway.common.fields import TimestampField
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.core.constants import GatewayKindNameEnum, GatewayStatusEnum, convert_gateway_kind_to_name
from apigateway.service.bk_itsm import ItsmPermissionApplyHelper
from apigateway.service.mcp import (
    build_mcp_server_detail_url,
    build_mcp_server_permission_approval_url,
)
from apigateway.utils import time

logger = logging.getLogger(__name__)


def _get_mcp_server_url_from_context(context, obj) -> str:
    least_privileges = context.get("least_privileges", {})
    least_privilege = least_privileges.get((obj.gateway.id, obj.stage.id), "")
    return MCPServerHandler.get_mcp_server_url(obj, least_privilege)


def _get_categories_from_context(context, obj) -> List[Dict[str, str]]:
    return context.get("categories", {}).get(obj.id, [])


class GatewayListInputSLZ(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)
    kind = serializers.ChoiceField(choices=GatewayKindNameEnum.get_choices(), required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayListInputSLZ"


class GatewayListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()
    kind = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return ResourcePermissionHandler.convert_gateway_maintainers_to_display_names(
            obj.tenant_mode,
            obj.tenant_id,
            obj.maintainers,
        )

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    def get_kind(self, obj):
        return convert_gateway_kind_to_name(obj.kind)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayListOutputSLZ"


class GatewayRetrieveOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    description = SerializerTranslatedField(default_field="description_i18n", allow_blank=True, read_only=True)
    maintainers = serializers.SerializerMethodField()
    doc_maintainers = serializers.SerializerMethodField()
    kind = serializers.SerializerMethodField()

    def get_maintainers(self, obj):
        return ResourcePermissionHandler.convert_gateway_maintainers_to_display_names(
            obj.tenant_mode,
            obj.tenant_id,
            obj.maintainers,
        )

    def get_doc_maintainers(self, obj):
        return obj.doc_maintainers

    def get_kind(self, obj):
        return convert_gateway_kind_to_name(obj.kind)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayRetrieveOutputSLZ"


class AppResourcePermissionListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(max_length=32, required=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppResourcePermissionListInputSLZ"


class AppGatewayPermissionInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(max_length=32, required=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppGatewayPermissionInputSLZ"


class AppGatewayPermissionOutputSLZ(serializers.Serializer):
    allow_apply_by_gateway = serializers.BooleanField(read_only=True)
    name = serializers.CharField(read_only=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppGatewayPermissionOutputSLZ"


class GatewayAppPermissionApplyCreateInputSLZ(serializers.Serializer):
    """
    PaaS中应用申请访问网关API的权限
    - 提供给 paas 开发者中心的接口
    - 应用页面申请授权，仅可申请限定有效期的权限，网关平台按规则主动续期权限
    """

    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        # validators=[ResourceIDValidator()], PaaS中的列表资源本身获取的就是网关所有环境生效资源版本资源的并集，这里不需要再进行校验
        allow_empty=True,
        required=False,
    )
    reason = serializers.CharField(allow_blank=True, required=False, default="")
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        default=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
    )
    grant_dimension = serializers.ChoiceField(choices=GrantDimensionEnum.get_choices())

    def validate(self, data):
        if data["grant_dimension"] == GrantDimensionEnum.RESOURCE.value and not data.get("resource_ids"):
            raise serializers.ValidationError(
                _("申请权限类型为 {grant_dimension} 时，参数 resource_ids 不能为空。").format(
                    grant_dimension=data["grant_dimension"]
                )
            )

        return data

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayAppPermissionApplyCreateInputSLZ"


class AppResourcePermissionListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(label="ID", read_only=True)
    name = serializers.CharField()
    gateway_name = serializers.CharField()
    gateway_id = serializers.IntegerField(required=False, allow_null=True)
    description = SerializerTranslatedField(translated_fields={"en": "description_en"})
    description_en = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    expires_in = serializers.SerializerMethodField()
    permission_level = serializers.CharField()
    permission_status = serializers.ChoiceField(choices=PermissionStatusEnum.get_choices())
    permission_action = serializers.SerializerMethodField()
    doc_link = serializers.CharField()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppResourcePermissionListOutputSLZ"

    def get_expires_in(self, obj):
        if math.isinf(obj["expires_in"]):
            return None

        return obj["expires_in"]

    def get_permission_action(self, obj):
        """
        支持的权限操作
        """
        if self._need_to_apply_permission(obj["permission_status"]):
            return PermissionActionEnum.APPLY.value

        if self._need_to_renew_permission(obj["permission_status"], obj["expires_in"]):
            return PermissionActionEnum.RENEW.value

        return ""

    def _need_to_apply_permission(self, permission_status):
        return permission_status not in [
            PermissionStatusEnum.PENDING.value,
            PermissionStatusEnum.OWNED.value,
            PermissionStatusEnum.UNLIMITED.value,
        ]

    def _need_to_renew_permission(self, permission_status, expires_in):
        renewable_end_time = time.to_seconds(days=RENEWABLE_EXPIRE_DAYS)
        if permission_status in [PermissionStatusEnum.OWNED.value] and 0 < expires_in < renewable_end_time:
            return True

        return False


class AppPermissionRenewInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    resource_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True,
        max_length=100,
    )
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        default=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
    )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRenewInputSLZ"


class AppPermissionListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    expire_days_range = serializers.IntegerField(min_value=0, allow_null=True, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionListInputSLZ"


class AppPermissionRecordListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    applied_by = serializers.CharField(allow_blank=True, required=False)
    applied_time_start = TimestampField(allow_null=True, required=False)
    applied_time_end = TimestampField(allow_null=True, required=False)
    apply_status = serializers.ChoiceField(choices=ApplyStatusEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordListInputSLZ"


class AppPermissionRecordRetrieveInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordRetrieveInputSLZ"


class AppPermissionRecordBaseSLZ(serializers.ModelSerializer):
    gateway_name = serializers.SerializerMethodField()
    apply_status = serializers.SerializerMethodField()
    apply_status_display = serializers.SerializerMethodField()
    handled_by = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    applied_by = serializers.SerializerMethodField()
    itsm_ticket_url = serializers.SerializerMethodField()

    class Meta:
        model = AppPermissionRecord
        fields = [
            "id",
            "bk_app_code",
            "applied_by",
            "applied_time",
            "handled_by",
            "handled_time",
            "apply_status",
            "apply_status_display",
            "grant_dimension",
            "comment",
            "reason",
            "expire_days",
            "itsm_ticket_id",
            "itsm_ticket_url",
            "gateway_name",
        ]
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordBaseSLZ"

    def get_gateway_name(self, obj):
        return obj.gateway.name

    def get_apply_status(self, obj):
        return obj.status

    def get_apply_status_display(self, obj):
        return ApplyStatusEnum.get_choice_label(obj.status)

    def get_handled_by(self, obj):
        if obj.handled_by:
            return [obj.handled_by]
        return obj.gateway.maintainers

    def get_comment(self, obj):
        return obj.comment or ""

    def get_applied_by(self, obj):
        return ResourcePermissionHandler.convert_applied_by_to_display_name(
            obj.bk_app_code,
            obj.applied_by,
            obj.gateway.tenant_mode,
            obj.gateway.tenant_id,
        )

    def get_itsm_ticket_url(self, obj):
        return ItsmPermissionApplyHelper.build_ticket_url(obj.itsm_ticket_id)


class AppPermissionRecordListOutputSLZ(AppPermissionRecordBaseSLZ):
    class Meta(AppPermissionRecordBaseSLZ.Meta):
        fields = AppPermissionRecordBaseSLZ.Meta.fields
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordListOutputSLZ"


class AppPermissionRecordOutputSLZ(AppPermissionRecordBaseSLZ):
    resources = serializers.SerializerMethodField()

    class Meta(AppPermissionRecordBaseSLZ.Meta):
        fields = AppPermissionRecordBaseSLZ.Meta.fields + ["resources"]
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordOutputSLZ"

    def get_resources(self, obj):
        if obj.grant_dimension == GrantDimensionEnum.API.value:
            return []

        resources = []
        for apply_status, resource_ids in self._get_handled_resource_ids(obj).items():
            for resource_id in resource_ids:
                resource = self.context["resource_id_map"].get(resource_id)
                resources.append(
                    {
                        "apply_status": apply_status,
                        "name": resource.name
                        if resource
                        else _("资源【{resource_id}】已删除。").format(resource_id=resource_id),
                    }
                )

        return sorted(resources, key=lambda x: (x["apply_status"], x["name"]))

    def _get_handled_resource_ids(self, obj):
        if obj.status == ApplyStatusEnum.PENDING.value:
            return {
                ApplyStatusEnum.PENDING.value: obj.resource_ids,
            }

        return obj.handled_resource_ids


class GatewayAppPermissionApplyCreateOutputSLZ(serializers.Serializer):
    record_id = serializers.IntegerField(read_only=True)
    itsm_ticket_id = serializers.CharField(read_only=True, allow_blank=True, default="")
    itsm_ticket_url = serializers.CharField(read_only=True, allow_blank=True, default="")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayAppPermissionApplyCreateOutputSLZ"


class MCPServerPermissionListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(required=True, validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")
    keyword = serializers.CharField(required=False, help_text="keyword")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerPermissionListInputSLZ"


class MCPServerBaseSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 中文名/显示名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")
    tools_count = serializers.CharField(read_only=True, help_text="MCPServer 工具数量")
    doc_link = serializers.SerializerMethodField(help_text="MCPServer 文档访问地址")
    tool_names = serializers.ListField(
        child=serializers.CharField(),
        help_text="工具名称列表",
    )
    protocol_type = serializers.ChoiceField(
        read_only=True,
        help_text="MCPServer 协议类型",
        choices=MCPServerProtocolTypeEnum.get_choices(),
    )
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")
    categories = serializers.SerializerMethodField(help_text="MCPServer 分类列表")
    is_official = serializers.SerializerMethodField(help_text="是否为官方")
    oauth2_public_client_enabled = serializers.BooleanField(
        read_only=True, help_text="是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权"
    )

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    def get_url(self, obj) -> str:
        return _get_mcp_server_url_from_context(self.context, obj)

    def get_doc_link(self, obj):
        return build_mcp_server_detail_url(obj.id)

    def get_categories(self, obj) -> List[Dict[str, str]]:
        return _get_categories_from_context(self.context, obj)

    def get_is_official(self, obj) -> bool:
        return any(
            cat["name"] == OFFICIAL_MCP_CATEGORY_NAME for cat in _get_categories_from_context(self.context, obj)
        )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerBaseSLZ"


class MCPServerPermissionBaseSLZ(serializers.Serializer):
    status = serializers.CharField(help_text="MCPServer 权限状态")
    action = serializers.CharField(help_text="MCPServer 权限操作")
    expires_in = serializers.IntegerField(help_text="MCPServer 权限过期时间")
    handled_by = serializers.ListField(child=serializers.CharField(), help_text="处理人")
    approval_url = serializers.SerializerMethodField(help_text="权限审批 URL")

    def get_approval_url(self, obj) -> str:
        """获取审批 URL"""
        try:
            if isinstance(obj, dict):
                mcp_server_id = obj.get("mcp_server_id")
                gateway_id = obj.get("gateway_id")
                itsm_ticket_id = obj.get("itsm_ticket_id", "")

                if gateway_id and mcp_server_id:
                    return build_mcp_server_permission_approval_url(gateway_id, mcp_server_id, itsm_ticket_id)

            # 如果是模型实例
            if hasattr(obj, "mcp_server"):
                return build_mcp_server_permission_approval_url(
                    obj.mcp_server.gateway_id, obj.mcp_server_id, getattr(obj, "itsm_ticket_id", "")
                )
        except Exception:
            # 记录错误但不中断响应
            logger.warning("Failed to build approval URL for object: %s", obj)

        return ""

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerPermissionBaseSLZ"


class MCPServerPermissionListOutputSLZ(serializers.Serializer):
    mcp_server = MCPServerBaseSLZ()
    permission = MCPServerPermissionBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerPermissionListOutputSLZ"


class MCPServerAppPermissionApplyCreateInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(required=True, validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")
    mcp_server_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True,
        max_length=50,
        help_text="MCPServer ID 列表，最多 50 个",
    )
    applied_by = serializers.CharField(required=True, help_text="申请人")
    reason = serializers.CharField(required=True, help_text="申请原因")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionApplyCreateInputSLZ"


class MCPServerAppPermissionApplyCreateOutputSLZ(serializers.Serializer):
    record_id = serializers.IntegerField(source="id", read_only=True, help_text="申请记录 ID")
    bk_app_code = serializers.CharField(read_only=True, help_text="蓝鲸应用 ID")
    mcp_server_id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    itsm_ticket_id = serializers.CharField(read_only=True, help_text="关联的 ITSM 工单 ID")
    approval_url = serializers.SerializerMethodField(help_text="权限审批 URL")

    def get_approval_url(self, obj) -> str:
        return build_mcp_server_permission_approval_url(
            obj.mcp_server.gateway_id, obj.mcp_server_id, obj.itsm_ticket_id or ""
        )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionApplyCreateOutputSLZ"


class MCPServerAppPermissionListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionListInputSLZ"


class MCPServerAppPermissionListOutputSLZ(serializers.Serializer):
    mcp_server = MCPServerBaseSLZ()
    permission = MCPServerPermissionBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionListOutputSLZ"


class MCPServerAppPermissionRecordListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")
    applied_by = serializers.CharField(allow_blank=True, required=False, help_text="申请人")
    applied_time_start = TimestampField(allow_null=True, required=False, help_text="申请时间开始")
    applied_time_end = TimestampField(allow_null=True, required=False, help_text="申请时间结束")
    apply_status = serializers.ChoiceField(
        choices=MCPServerAppPermissionApplyStatusEnum.get_choices(),
        allow_blank=True,
        required=False,
        help_text="申请状态",
    )
    query = serializers.CharField(allow_blank=True, required=False, help_text="MCPServer 名称")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionRecordListInputSLZ"


class MCPServerAppPermissionRecordBaseSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    applied_by = serializers.SerializerMethodField(help_text="申请人")
    applied_time = serializers.DateTimeField(read_only=True, help_text="申请时间")
    handled_by = serializers.ListField(child=serializers.CharField(), help_text="处理人")
    handled_time = serializers.DateTimeField(read_only=True, help_text="处理时间")
    apply_status = serializers.CharField(read_only=True, help_text="审批状态")
    apply_status_display = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True, help_text="备注")
    reason = serializers.CharField(read_only=True, help_text="申请原因")
    expire_days = serializers.IntegerField(read_only=True, help_text="过期天数")
    itsm_ticket_id = serializers.CharField(read_only=True, help_text="关联的 ITSM 工单 ID")
    approval_url = serializers.SerializerMethodField(help_text="权限审批 URL")

    def get_approval_url(self, obj) -> str:
        """获取审批 URL"""
        try:
            if isinstance(obj, dict):
                mcp_server_id = obj.get("mcp_server_id")
                gateway_id = obj.get("gateway_id")
                itsm_ticket_id = obj.get("itsm_ticket_id", "")

                if gateway_id and mcp_server_id:
                    return build_mcp_server_permission_approval_url(gateway_id, mcp_server_id, itsm_ticket_id)

            # 如果是模型实例
            if hasattr(obj, "mcp_server"):
                return build_mcp_server_permission_approval_url(
                    obj.mcp_server.gateway_id, obj.mcp_server_id, getattr(obj, "itsm_ticket_id", "")
                )
        except Exception:
            # 记录错误但不中断响应
            logger.warning("Failed to build approval URL for object: %s", obj)

        return ""

    def get_applied_by(self, obj):
        """获取申请人 display_name"""
        if isinstance(obj, dict):
            try:
                return ResourcePermissionHandler.convert_applied_by_to_display_name(
                    obj.get("bk_app_code", ""),
                    obj.get("applied_by", ""),
                    obj.get("tenant_mode", ""),
                    obj.get("tenant_id", ""),
                )
            except Exception:
                logger.warning("Failed to convert applied_by for dict object: %s", obj, exc_info=True)
                return obj.get("applied_by", "")

        if hasattr(obj, "mcp_server"):
            try:
                return ResourcePermissionHandler.convert_applied_by_to_display_name(
                    obj.bk_app_code,
                    obj.applied_by,
                    obj.mcp_server.gateway.tenant_mode,
                    obj.mcp_server.gateway.tenant_id,
                )
            except Exception:
                logger.warning("Failed to convert applied_by for model object: %s", obj, exc_info=True)
                return getattr(obj, "applied_by", "")

        return getattr(obj, "applied_by", "")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionRecordBaseSLZ"


class MCPServerAppPermissionRecordListOutputSLZ(serializers.Serializer):
    mcp_server = MCPServerBaseSLZ()
    record = MCPServerAppPermissionRecordBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionRecordListOutputSLZ"


class MCPServerAppPermissionRecordRetrieveInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(validators=[BKAppCodeValidator()], help_text="蓝鲸应用 ID")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionRecordRetrieveInputSLZ"


class MCPServerAppPermissionRecordRetrieveOutputSLZ(serializers.Serializer):
    mcp_server = MCPServerBaseSLZ()
    record = MCPServerAppPermissionRecordBaseSLZ()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionRecordRetrieveOutputSLZ"


class MCPServerListInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer 筛选条件，支持模糊匹配 MCPServer 名称或描述"
    )
    order_by = serializers.CharField(
        allow_blank=True,
        required=False,
        default="-updated_time",
        help_text="排序字段，支持 id, name, updated_time, created_time，前缀 - 表示降序，默认 -updated_time",
    )
    mcp_server_ids = serializers.CharField(
        allow_blank=True, required=False, help_text="MCPServer ID 列表，多个以逗号 , 分割"
    )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerListInputSLZ"

    def validate_mcp_server_ids(self, value):
        if not value:
            return []
        try:
            ids = [int(x.strip()) for x in value.split(",")]
        except ValueError:
            raise serializers.ValidationError(_("MCPServer ID 必须为整数，多个以逗号分割"))
        if len(ids) > 50:
            raise serializers.ValidationError(_("MCPServer ID 列表最多支持 50 个"))
        return ids


class MCPServerListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="MCPServer ID")
    name = serializers.CharField(read_only=True, help_text="MCPServer 名称")
    title = serializers.SerializerMethodField(help_text="MCPServer 中文名/显示名称")
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")

    is_public = serializers.BooleanField(read_only=True, help_text="MCPServer 是否公开")

    labels = serializers.ListField(read_only=True, help_text="MCPServer 标签")
    resource_names = serializers.ListField(read_only=True, help_text="MCPServer 资源名称")
    tool_names = serializers.ListField(read_only=True, help_text="MCPServer 工具名称列表")

    status = serializers.CharField(read_only=True, help_text="MCPServer 状态")

    protocol_type = serializers.ChoiceField(
        read_only=True,
        help_text="MCPServer 协议类型",
        choices=MCPServerProtocolTypeEnum.get_choices(),
    )

    oauth2_public_client_enabled = serializers.BooleanField(
        read_only=True, help_text="是否开启 OAuth2 公开客户端模式，开启后将会对 bk_app_code=public 的应用进行授权"
    )

    categories = serializers.SerializerMethodField(help_text="MCPServer 分类列表")

    stage = serializers.SerializerMethodField(help_text="MCPServer 环境")
    gateway = serializers.SerializerMethodField(help_text="MCPServer 网关")

    tools_count = serializers.IntegerField(read_only=True, help_text="MCPServer 工具数量")
    prompts_count = serializers.SerializerMethodField(help_text="MCPServer Prompts 数量")
    url = serializers.SerializerMethodField(help_text="MCPServer 访问 URL")
    detail_url = serializers.SerializerMethodField(help_text="MCPServer 网关站点详情 URL")

    updated_by = serializers.CharField(read_only=True, help_text="更新人")
    created_by = serializers.CharField(read_only=True, help_text="创建人")
    updated_time = serializers.DateTimeField(read_only=True, help_text="更新时间")
    created_time = serializers.DateTimeField(read_only=True, help_text="创建时间")

    def get_title(self, obj) -> str:
        return obj.title if obj.title else obj.name

    def get_categories(self, obj) -> List[Dict[str, str]]:
        return _get_categories_from_context(self.context, obj)

    def get_stage(self, obj):
        return self.context["stages"][obj.stage.id]

    def get_gateway(self, obj):
        return self.context["gateways"][obj.gateway.id]

    def get_url(self, obj) -> str:
        return _get_mcp_server_url_from_context(self.context, obj)

    def get_detail_url(self, obj) -> str:
        return build_mcp_server_detail_url(obj.id)

    def get_prompts_count(self, obj) -> int:
        prompts_count_map = self.context.get("prompts_count_map", {})
        return prompts_count_map.get(obj.id, 0)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerListOutputSLZ"


# ===================== Gateway 下架/删除相关序列化器 =====================


class ItsmCallbackTicketFormDataSLZ(serializers.Serializer):
    apply_record_id = serializers.IntegerField(required=True, help_text="权限申请记录 ID")
    grant_dimension = serializers.ChoiceField(
        required=True,
        choices=FormattedGrantDimensionEnum.get_choices(),
        help_text="授权维度",
    )


class ItsmCallbackTicketSLZ(serializers.Serializer):
    id = serializers.CharField(required=True, help_text="ITSM 工单 ID")
    approve_result = serializers.BooleanField(required=True, help_text="审批结果")
    form_data = ItsmCallbackTicketFormDataSLZ(required=True, help_text="工单表单数据")


class ItsmCallbackInputSLZ(serializers.Serializer):
    callback_token = serializers.CharField(required=True, allow_blank=False, help_text="回调 token")
    ticket = ItsmCallbackTicketSLZ(required=True, help_text="工单详情")


class GatewayUpdateStatusInputSLZ(serializers.Serializer):
    """网关状态更新输入序列化器（用于下架/停用网关）"""

    status = serializers.ChoiceField(
        choices=GatewayStatusEnum.get_choices(),
        help_text="网关状态，0：停用，1：启用",
    )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayUpdateStatusInputSLZ"


class MonitorCallbackInputSLZ(serializers.Serializer):
    """监控告警回调参数校验（query params 中的 token）"""

    token = serializers.CharField(max_length=64, required=True, allow_blank=False)

    def validate_token(self, value: str) -> str:
        if value != getattr(settings, "BKMONITOR_CALLBACK_TOKEN", None):
            raise serializers.ValidationError("token 验证失败")
        return value


class MonitorCallbackRequestBodySLZ(serializers.Serializer):
    """监控告警回调请求体（透传 BkMonitor 告警内容，结构不固定）"""

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MonitorCallbackRequestBodySLZ"


class AppAlarmRecordListInputSLZ(serializers.Serializer):
    status = serializers.ChoiceField(
        choices=AlarmStatusEnum.get_choices(),
        allow_blank=True,
        required=False,
        help_text="告警状态",
    )
    gateway_name = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="网关名称（精确匹配）",
    )
    resource_name = serializers.CharField(
        allow_blank=True,
        required=False,
        help_text="资源名称（精确匹配）",
    )
    time_start = TimestampField(required=True, help_text="开始时间")
    time_end = TimestampField(required=True, help_text="结束时间")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppAlarmRecordListInputSLZ"

    def validate(self, attrs):
        time_start = attrs.get("time_start")
        time_end = attrs.get("time_end")
        if not (time_start and time_end):
            raise serializers.ValidationError(_("参数 time_start 和 time_end 需要同时提供。"))

        if attrs.get("resource_name") and not attrs.get("gateway_name"):
            raise serializers.ValidationError({"gateway_name": _("传 resource_name 时，必须同时传 gateway_name。")})

        return attrs


class AppAlarmRecordListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    alarm_id = serializers.CharField(read_only=True)
    status = serializers.CharField(read_only=True)
    status_display = serializers.CharField(read_only=True)
    created_time = serializers.DateTimeField(read_only=True)
    gateway_name = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    stage = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    resource_id = serializers.IntegerField(read_only=True, allow_null=True)
    resource_name = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    request_id = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)
    message = serializers.CharField(read_only=True, allow_blank=True, allow_null=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppAlarmRecordListOutputSLZ"


class AppRequestLogListInputSLZ(serializers.Serializer):
    gateway_name = serializers.CharField(allow_blank=True, required=False, help_text="网关名称（精确匹配）")
    resource_name = serializers.CharField(allow_blank=True, required=False, help_text="资源名称（精确匹配）")
    request_id = serializers.CharField(allow_blank=True, required=False, help_text="请求 ID")
    status = serializers.IntegerField(required=False, min_value=100, max_value=599, help_text="响应状态码")
    time_start = TimestampField(label="起始时间", required=True, help_text="起始时间")
    time_end = TimestampField(label="结束时间", required=True, help_text="结束时间")
    offset = serializers.IntegerField(label="偏移量", required=False, min_value=0, default=0, help_text="偏移量")
    limit = serializers.IntegerField(
        label="限制条数",
        required=False,
        min_value=1,
        max_value=100,
        default=10,
        help_text="限制条数",
    )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppRequestLogListInputSLZ"

    def validate(self, attrs):
        max_time_range_days = 180
        time_start = attrs["time_start"]
        time_end = attrs["time_end"]
        now = time.to_datetime_from_now()
        min_time_start = time.to_datetime_from_now(days=-max_time_range_days)

        if time_start < min_time_start:
            raise serializers.ValidationError(
                {"time_start": _("time_start must be within the last {days} days.").format(days=max_time_range_days)}
            )

        if time_end <= time_start:
            raise serializers.ValidationError({"time_end": _("time_end must be greater than time_start.")})

        if time_end >= now:
            raise serializers.ValidationError({"time_end": _("time_end must be less than current time.")})

        return attrs


class AppRequestLogListOutputSLZ(serializers.Serializer):
    request_id = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求 ID")
    timestamp = serializers.IntegerField(required=False, allow_null=True, help_text="请求时间戳")
    gateway_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="网关名称")
    stage = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="环境")
    resource_id = serializers.IntegerField(required=False, allow_null=True, help_text="资源 ID")
    resource_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="资源名称")
    method = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求方法")
    http_host = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求域名")
    http_path = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="请求路径")
    status = serializers.IntegerField(required=False, allow_null=True, help_text="响应状态码")
    request_duration = serializers.IntegerField(required=False, allow_null=True, help_text="请求耗时")
    code_name = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="状态码名称")
    error = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="错误")
    response_desc = serializers.CharField(required=False, allow_null=True, allow_blank=True, help_text="响应描述")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppRequestLogListOutputSLZ"
