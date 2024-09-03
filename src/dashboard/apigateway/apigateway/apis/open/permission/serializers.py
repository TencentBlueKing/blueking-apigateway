# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from apigateway.apps.permission.constants import (
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    GrantDimensionEnum,
    PermissionActionEnum,
    PermissionApplyExpireDaysEnum,
    PermissionStatusEnum,
)
from apigateway.apps.permission.models import AppPermissionRecord
from apigateway.biz.permission import PermissionDimensionManager
from apigateway.biz.validators import BKAppCodeValidator
from apigateway.common.fields import TimestampField
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.utils import time


class AppResourcePermissionInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(max_length=32, required=True)


class AppGatewayPermissionInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(max_length=32, required=True)


class AppResourcePermissionOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField(label="ID", read_only=True)
    name = serializers.CharField()
    api_name = serializers.CharField()
    gateway_id = serializers.IntegerField(required=False, allow_null=True)
    description = SerializerTranslatedField(translated_fields={"en": "description_en"})
    description_en = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    expires_in = serializers.SerializerMethodField()
    permission_level = serializers.CharField()
    permission_status = serializers.ChoiceField(choices=PermissionStatusEnum.get_choices())
    permission_action = serializers.SerializerMethodField()
    doc_link = serializers.CharField()

    class Meta:
        ref_name = "apigateway.apis.open.permission.serializers.AppResourcePermissionOutputSLZ"

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


class PaaSAppPermissionApplyInputSLZ(serializers.Serializer):
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


class GatewayResourceIDs(serializers.Serializer):
    gateway_id = serializers.IntegerField(
        help_text="gateway_id",
        required=True,
    )
    resource_ids = serializers.ListField(
        help_text="如果不传则为网关维度申请",
        child=serializers.IntegerField(),
        allow_empty=True,
        required=False,
        max_length=100,
    )


class PaaSAppPermissionApplyV2InputSLZ(serializers.Serializer):
    """
    PaaS中应用申请访问网关API的权限
    - 提供给 paas 开发者中心的接口
    - 应用页面申请授权,支持网关+resource维度
    """

    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    gateway_resource_ids = serializers.ListField(
        help_text="申请资源id列表(资源+网关)",
        child=GatewayResourceIDs(),
        allow_empty=False,
        required=True,
        max_length=100,
    )
    reason = serializers.CharField(allow_blank=True, required=False, default="")
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        default=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
    )


class AppPermissionApplyV1InputSLZ(serializers.Serializer):
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


class GrantAppPermissionInputSLZ(serializers.Serializer):
    """
    网关关联应用，主动为应用授权访问网关API的权限
    """

    # 主动授权时，应用可能尚未创建，因此不校验 app_code 是否存在
    target_app_code = serializers.CharField(label="", max_length=32, required=True)
    expire_days = serializers.IntegerField(required=False)
    grant_dimension = serializers.ChoiceField(choices=GrantDimensionEnum.get_choices())
    resource_names = serializers.ListField(
        child=serializers.CharField(required=True), allow_empty=True, required=False
    )


class RevokeAppPermissionInputSLZ(serializers.Serializer):
    """回收应用访问网关的权限"""

    target_app_codes = serializers.ListField(
        child=serializers.CharField(max_length=32, required=True), allow_empty=False
    )
    grant_dimension = serializers.ChoiceField(choices=[GrantDimensionEnum.API.value])


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


class AppPermissionInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    expire_days_range = serializers.IntegerField(min_value=0, allow_null=True, required=False)


class AppPermissionRecordInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    applied_by = serializers.CharField(allow_blank=True, required=False)
    applied_time_start = TimestampField(allow_null=True, required=False)
    applied_time_end = TimestampField(allow_null=True, required=False)
    apply_status = serializers.ChoiceField(choices=ApplyStatusEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)


class AppPermissionRecordSLZ(serializers.ModelSerializer):
    api_name = serializers.SerializerMethodField()
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
            "api_name",
        ]

    def get_api_name(self, obj):
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


class AppPermissionRecordOutputSLZ(AppPermissionRecordSLZ):
    resources = serializers.SerializerMethodField()

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
            "api_name",
            "resources",
        ]

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
