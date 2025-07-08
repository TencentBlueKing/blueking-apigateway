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

from django.conf import settings
from rest_framework import serializers

from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord
from apigateway.apps.esb.helpers import BoardConfigManager
from apigateway.apps.esb.validators import ComponentIDValidator
from apigateway.apps.permission.constants import (
    RENEWABLE_EXPIRE_DAYS,
    ApplyStatusEnum,
    PermissionActionEnum,
    PermissionApplyExpireDaysEnum,
    PermissionStatusEnum,
)
from apigateway.biz.validators import BKAppCodeValidator
from apigateway.common.fields import TimestampField
from apigateway.common.i18n.field import SerializerTranslatedField
from apigateway.utils import time


class AppPermissionComponentQuerySLZ(serializers.Serializer):
    target_app_code = serializers.CharField(max_length=32, required=True)


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


class AppPermissionApplySLZ(serializers.Serializer):
    # TODO 验证当前用户为 target_app_code 管理员
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    component_ids = serializers.ListField(
        child=serializers.IntegerField(),
        validators=[ComponentIDValidator()],
        allow_empty=False,
        required=True,
    )
    reason = serializers.CharField(allow_blank=True, required=False, default="")
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        default=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
    )


class AppPermissionRenewSLZ(serializers.Serializer):
    # TODO 验证当前用户为 target_app_code 管理员
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    component_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        required=True,
        max_length=100,
    )
    expire_days = serializers.ChoiceField(
        choices=PermissionApplyExpireDaysEnum.get_choices(),
        default=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
    )


class AppPermissionQuerySLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    expire_days_range = serializers.IntegerField(min_value=0, allow_null=True, required=False)


class AppPermissionApplyRecordQuerySLZ(serializers.Serializer):
    target_app_code = serializers.CharField(label="", validators=[BKAppCodeValidator()])
    applied_by = serializers.CharField(allow_blank=True, required=False)
    applied_time_start = TimestampField(allow_null=True, required=False)
    applied_time_end = TimestampField(allow_null=True, required=False)
    apply_status = serializers.ChoiceField(choices=ApplyStatusEnum.get_choices(), allow_blank=True, required=False)
    query = serializers.CharField(allow_blank=True, required=False)


class ComponentInRecordSLZ(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    description = SerializerTranslatedField(translated_fields={"en": "description_en"})
    description_en = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    apply_status = serializers.CharField()


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


class AppPermissionApplyRecordV1SLZ(AppPermissionApplyRecordSLZ):
    components = None

    class Meta(AppPermissionApplyRecordSLZ.Meta):
        fields = AppPermissionApplyRecordSLZ.Meta._common_fields


class AppPermissionApplyRecordDetailSLZ(AppPermissionApplyRecordSLZ):
    class Meta(AppPermissionApplyRecordSLZ.Meta):
        fields = AppPermissionApplyRecordSLZ.Meta._common_fields + ["components"]
