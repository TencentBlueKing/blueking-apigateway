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

from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apis.open.esb.permission.serializers import ComponentInRecordSLZ
from apigateway.apis.web.constants import UserAuthTypeEnum
from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord
from apigateway.apps.esb.helpers import BoardConfigManager
from apigateway.apps.esb.utils import get_related_boards
from apigateway.apps.esb.validators import ComponentIDValidator
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
    allow_apply_by_api = serializers.BooleanField(read_only=True)
    name = serializers.CharField(read_only=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppGatewayPermissionInputSLZ"


class PaaSAppPermissionApplyCreateInputSLZ(serializers.Serializer):
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
        ref_name = "apigateway.apis.v2.inner.serializers.PaaSAppPermissionApplyInputSLZ"


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


class AppPermissionRenewPutInputSLZ(serializers.Serializer):
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
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRenewPutInputSLZ"


class AppPermissionListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    expire_days_range = serializers.IntegerField(min_value=0, allow_null=True, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionInputSLZ"


class AppPermissionRecordListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    applied_by = serializers.CharField(allow_blank=True, required=False)
    applied_time_start = TimestampField(allow_null=True, required=False)
    applied_time_end = TimestampField(allow_null=True, required=False)
    apply_status = serializers.ChoiceField(choices=ApplyStatusEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordInputSLZ"


class AppPermissionRecordRetrieveInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordRetrieveInputSLZ"


class AppPermissionRecordSLZ(serializers.ModelSerializer):
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
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordSLZ"

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


class AppPermissionRecordListOutputSLZ(AppPermissionRecordSLZ):
    class Meta(AppPermissionRecordSLZ.Meta):
        fields = AppPermissionRecordSLZ.Meta.fields
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionRecordListOutputSLZ"


class AppPermissionRecordOutputSLZ(AppPermissionRecordSLZ):
    resources = serializers.SerializerMethodField()

    class Meta(AppPermissionRecordSLZ.Meta):
        fields = AppPermissionRecordSLZ.Meta.fields + ["resources"]
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


class EsbSystemListInputSLZ(serializers.Serializer):
    user_auth_type = serializers.ChoiceField(choices=UserAuthTypeEnum.get_choices())

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbSystemListInputSLZ"

    def to_internal_value(self, data):
        data = super().to_internal_value(data)
        data["boards"] = get_related_boards(data["user_auth_type"])
        return data


class EsbSystemListOutputSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"}, allow_blank=True)
    description_en = serializers.CharField(required=False)
    maintainers = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbSystemListOutputSLZ"

    def get_maintainers(self, obj):
        """获取 ESB 系统的管理员"""
        return settings.ESB_MANAGERS

    def get_tag(self, obj):
        return BoardConfigManager.get_optional_display_label(obj.board)


class AppPermissionSLZ(serializers.Serializer):
    # TODO 验证当前用户为 target_app_code 管理员

    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        default=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
    )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionSLZ"


class EsbAppPermissionApplyCreateInputSLZ(AppPermissionSLZ):
    component_ids = serializers.ListField(
        child=serializers.IntegerField(),
        validators=[ComponentIDValidator()],
        allow_empty=False,
        required=True,
    )
    reason = serializers.CharField(allow_blank=True, required=False, default="")

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionApplyCreateInputSLZ"


class EsbAppPermissionRenewPutInputSLZ(AppPermissionSLZ):
    component_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True,
        max_length=100,
    )

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionRenewPutInputSLZ"


class AppPermissionApplyCreateOutputSLZ(serializers.Serializer):
    record_id = serializers.IntegerField(read_only=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionApplyCreateOutputSLZ"


class EsbAppPermissionListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    expire_days_range = serializers.IntegerField(min_value=0, allow_null=True, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionListInputSLZ"


class AppPermissionComponentSLZ(serializers.Serializer):
    id = serializers.IntegerField(label="ID", read_only=True)
    name = serializers.CharField()
    system_name = serializers.CharField()
    system_id = serializers.IntegerField(required=False, allow_null=True)
    description = SerializerTranslatedField(translated_fields={"en": "description_en"})
    description_en = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    expires_in = serializers.SerializerMethodField()
    permission_level = serializers.CharField()
    permission_status = serializers.ChoiceField(choices=PermissionStatusEnum.get_choices())
    permission_action = serializers.SerializerMethodField()
    doc_link = serializers.CharField()
    tag = serializers.SerializerMethodField()

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionComponentSLZ"

    def get_expires_in(self, obj):
        if math.isinf(obj["expires_in"]):
            return None

        return obj["expires_in"]

    def get_tag(self, obj):
        return BoardConfigManager.get_optional_display_label(obj["board"])

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
            PermissionStatusEnum.EXPIRED.value,
        ]

    def _need_to_renew_permission(self, permission_status, expires_in):
        renewable_end_time = time.to_seconds(days=RENEWABLE_EXPIRE_DAYS)
        # 对于已经过期的权限也可以申请续期
        if (
            permission_status in [PermissionStatusEnum.OWNED.value, PermissionStatusEnum.EXPIRED.value]
            and expires_in < renewable_end_time
        ):
            return True

        return False


class EsbPermissionComponentListOutputSLZ(AppPermissionComponentSLZ):
    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbPermissionComponentListOutputSLZ"


class EsbAppPermissionOutputSLZ(AppPermissionComponentSLZ):
    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionOutputSLZ"


class EsbPermissionComponentListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(max_length=32, required=True)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbPermissionComponentListInputSLZ"


class EsbAppPermissionApplyRecordListInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    applied_by = serializers.CharField(allow_blank=True, required=False)
    applied_time_start = TimestampField(allow_null=True, required=False)
    applied_time_end = TimestampField(allow_null=True, required=False)
    apply_status = serializers.ChoiceField(choices=ApplyStatusEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionApplyRecordListInputSLZ"


class AppPermissionApplyRecordSLZ(serializers.ModelSerializer):
    system_name = serializers.CharField(read_only=True)
    apply_status = serializers.CharField(read_only=True)
    apply_status_display = serializers.SerializerMethodField()
    handled_by = serializers.SerializerMethodField()
    comment = serializers.SerializerMethodField()
    tag = serializers.SerializerMethodField()
    components = serializers.ListField(child=ComponentInRecordSLZ())

    class Meta:
        model = AppPermissionApplyRecord
        _common_fields = [
            "id",
            "bk_app_code",
            "applied_by",
            "applied_time",
            "handled_by",
            "handled_time",
            "apply_status",
            "apply_status_display",
            "comment",
            "reason",
            "expire_days",
            "system_name",
        ]
        fields = _common_fields + ["tag", "components"]
        ref_name = "apigateway.apis.v2.inner.serializers.AppPermissionApplyRecordSLZ"

    def get_apply_status_display(self, obj):
        return ApplyStatusEnum.get_choice_label(obj.apply_status)

    def get_handled_by(self, obj):
        if obj.handled_by:
            return [obj.handled_by]
        return settings.ESB_MANAGERS

    def get_comment(self, obj):
        return obj.comment or ""

    def get_tag(self, obj):
        return BoardConfigManager.get_optional_display_label(obj.board)


class EsbAppPermissionApplyRecordListOutputSLZ(AppPermissionApplyRecordSLZ):
    components = None

    class Meta(AppPermissionApplyRecordSLZ.Meta):
        fields = AppPermissionApplyRecordSLZ.Meta._common_fields
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionApplyRecordListOutputSLZ"


class EsbAppPermissionApplyRecordRetrieveOutputSLZ(AppPermissionApplyRecordSLZ):
    class Meta(AppPermissionApplyRecordSLZ.Meta):
        fields = AppPermissionApplyRecordSLZ.Meta._common_fields + ["components"]
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionApplyRecordRetrieveOutputSLZ"


class EsbAppPermissionApplyRecordRetrieveInputSLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])

    class Meta:
        ref_name = "apigateway.apis.v2.inner.serializers.EsbAppPermissionApplyRecordRetrieveInputSLZ"
