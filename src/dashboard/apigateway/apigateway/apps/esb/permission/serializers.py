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
from django.conf import settings
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord
from apigateway.apps.esb.helpers import BoardConfigManager
from apigateway.apps.permission.constants import RENEWABLE_EXPIRE_DAYS, ApplyStatusEnum
from apigateway.common.fields import TimestampField
from apigateway.tencent_apigateway_common.i18n.field import SerializerTranslatedField
from apigateway.utils.time import to_datetime_from_now


class QueryAppPermissionSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(allow_blank=True, required=False)
    system_id = serializers.IntegerField(allow_null=True, required=False)
    component_id = serializers.IntegerField(allow_null=True, required=False)


class ESBAppPermissionListSLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    bk_app_code = serializers.CharField(max_length=32, required=True)
    system_name = serializers.SerializerMethodField()
    component_name = serializers.SerializerMethodField()
    component_description = serializers.SerializerMethodField()
    expires = serializers.DateTimeField(allow_null=True, required=False, source="expires_display")
    renewable = serializers.SerializerMethodField()

    def _get_component(self, component_id: int) -> dict:
        return self.context["component_map"].get(component_id)

    def get_system_name(self, obj):
        component = self._get_component(obj.component_id)
        return component["system_name"] if component else ""

    def get_component_name(self, obj):
        component = self._get_component(obj.component_id)
        return (
            component["name"]
            if component
            else _("组件【id={component_id}】已删除。").format(component_id=obj.component_id)
        )

    def get_component_description(self, obj):
        component = self._get_component(obj.component_id)
        return component["description"] if component else ""

    def get_renewable(self, obj):
        return bool(obj.expires and obj.expires < to_datetime_from_now(days=RENEWABLE_EXPIRE_DAYS))


class QueryAppPermissionApplyRecordSLZ(serializers.Serializer):
    bk_app_code = serializers.CharField(allow_blank=True, required=False)
    applied_by = serializers.CharField(allow_blank=True, required=False)
    handled_time_start = TimestampField(allow_null=True, required=False)
    handled_time_end = TimestampField(allow_null=True, required=False)


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


class AppPermissionApplyRecordDetailSLZ(AppPermissionApplyRecordSLZ):
    class Meta(AppPermissionApplyRecordSLZ.Meta):
        fields = AppPermissionApplyRecordSLZ.Meta._common_fields + ["components"]


class BatchHandleAppPermissionApplyRecordSLZ(serializers.Serializer):
    """批量审批"""

    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    part_component_ids = serializers.DictField(
        label="部分审批组件ID",
        child=serializers.ListField(child=serializers.IntegerField(), allow_empty=False),
        allow_empty=True,
        required=False,
    )
    status = serializers.ChoiceField(
        choices=[
            ApplyStatusEnum.PARTIAL_APPROVED.value,
            ApplyStatusEnum.APPROVED.value,
            ApplyStatusEnum.REJECTED.value,
        ]
    )
    comment = serializers.CharField(allow_blank=True, max_length=512)


class BatchAppComponentPermissionSLZ(serializers.Serializer):
    ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=False, required=True)
