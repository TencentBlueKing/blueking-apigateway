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
import math

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
)
from apigateway.apps.permission.constants import (
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    GrantDimensionEnum,
    PermissionActionEnum,
    PermissionApplyExpireDaysEnum,
    PermissionStatusEnum,
)
from apigateway.apps.permission.models import AppPermissionRecord
from apigateway.biz.validators import BKAppCodeValidator
from apigateway.common.fields import TimestampField
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.service.mcp.mcp_server import build_mcp_server_detail_url
from apigateway.utils import time


class GatewayListInputSLZ(serializers.Serializer):
    name = serializers.CharField(required=False, allow_blank=True)
    fuzzy = serializers.BooleanField(required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayListInputSLZ"


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
        ref_name = "apigateway.apis.v2.inner.serializers.GatewayListOutputSLZ"


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
    description = serializers.CharField(read_only=True, help_text="MCPServer 描述")
    tools_count = serializers.CharField(read_only=True, help_text="MCPServer 工具数量")
    doc_link = serializers.SerializerMethodField(help_text="MCPServer 文档访问地址")
    tool_names = serializers.ListField(
        child=serializers.CharField(),
        help_text="工具名称列表",
    )

    def get_doc_link(self, obj):
        return build_mcp_server_detail_url(obj["id"])

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerBaseSLZ"


class MCPServerPermissionBaseSLZ(serializers.Serializer):
    status = serializers.CharField(help_text="MCPServer 权限状态")
    action = serializers.CharField(help_text="MCPServer 权限操作")
    expires_in = serializers.IntegerField(help_text="MCPServer 权限过期时间")
    handled_by = serializers.ListField(child=serializers.CharField(), help_text="处理人")

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
    )
    applied_by = serializers.CharField(required=True, help_text="申请人")
    reason = serializers.CharField(required=True, help_text="申请原因")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.MCPServerAppPermissionApplyCreateInputSLZ"


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
    applied_by = serializers.CharField(read_only=True, help_text="申请人")
    applied_time = serializers.DateTimeField(read_only=True, help_text="申请时间")
    handled_by = serializers.ListField(child=serializers.CharField(), help_text="处理人")
    handled_time = serializers.DateTimeField(read_only=True, help_text="处理时间")
    apply_status = serializers.CharField(read_only=True, help_text="审批状态")
    apply_status_display = serializers.CharField(read_only=True)
    comment = serializers.CharField(read_only=True, help_text="备注")
    reason = serializers.CharField(read_only=True, help_text="申请原因")
    expire_days = serializers.IntegerField(read_only=True, help_text="过期天数")

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
