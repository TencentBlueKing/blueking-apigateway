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
import json
import operator

from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.label.models import APILabel
from apigateway.apps.monitor.constants import DETECT_METHOD_CHOICES, AlarmStatusEnum, NoticeRoleEnum, NoticeWayEnum
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.common.fields import CurrentGatewayDefault, TimestampField


class DetectConfigSLZ(serializers.Serializer):
    duration = serializers.IntegerField(min_value=1)
    method = serializers.ChoiceField(choices=DETECT_METHOD_CHOICES)
    count = serializers.IntegerField(min_value=0)


class ConvergeConfigSLZ(serializers.Serializer):
    duration = serializers.IntegerField(min_value=0)


class NoticeConfigSLZ(serializers.Serializer):
    notice_way = serializers.ListField(
        child=serializers.ChoiceField(choices=NoticeWayEnum.get_choices()),
    )
    notice_role = serializers.ListField(
        child=serializers.ChoiceField(choices=NoticeRoleEnum.get_choices()),
        allow_empty=True,
    )
    notice_extra_receiver = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
    )

    def validate(self, data):
        if not (data.get("notice_role") or data.get("notice_extra_receiver")):
            raise serializers.ValidationError(_("通知对象、其他通知对象不能同时为空。"))
        return data


class AlarmStrategyConfigSLZ(serializers.Serializer):
    detect_config = DetectConfigSLZ()
    converge_config = ConvergeConfigSLZ()
    notice_config = NoticeConfigSLZ()


class AlarmStrategyInputSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault())
    gateway_label_ids = serializers.ListField(child=serializers.IntegerField(), allow_empty=True)
    config = AlarmStrategyConfigSLZ()

    class Meta:
        model = AlarmStrategy
        fields = [
            "gateway",
            "id",
            "name",
            "alarm_type",
            "alarm_subtype",
            "gateway_label_ids",
            "config",
        ]
        lookup_field = "id"

    def validate_config(self, value):
        # does not support writable nested fields by default
        return json.dumps(value)

    def validate_gateway_label_ids(self, value):
        gateway = self.context["request"].gateway
        return list(APILabel.objects.filter(gateway=gateway, id__in=value or []).values_list("id", flat=True))


class AlarmStrategyListOutputSLZ(serializers.ModelSerializer):
    gateway_labels = serializers.SerializerMethodField()

    class Meta:
        model = AlarmStrategy
        fields = [
            "id",
            "name",
            "alarm_type",
            "alarm_subtype",
            "enabled",
            "updated_time",
            "gateway_labels",
        ]
        lookup_field = "id"

    def get_gateway_labels(self, obj):
        return sorted(obj.api_labels.values("id", "name"), key=operator.itemgetter("name"))


class AlarmStrategyUpdateStatusInputSLZ(serializers.ModelSerializer):
    class Meta:
        model = AlarmStrategy
        fields = [
            "enabled",
        ]
        lookup_field = "id"


class AlarmRecordQueryInputSLZ(serializers.Serializer):
    time_start = TimestampField(allow_null=True, required=False)
    time_end = TimestampField(allow_null=True, required=False)
    alarm_strategy_id = serializers.IntegerField(allow_null=True, required=False)
    status = serializers.ChoiceField(choices=AlarmStatusEnum.get_choices(), allow_blank=True, required=False)


class AlarmRecordQueryOutputSLZ(serializers.ModelSerializer):
    alarm_strategy_names = serializers.SerializerMethodField()

    class Meta:
        model = AlarmRecord
        fields = [
            "id",
            "alarm_id",
            "status",
            "message",
            "created_time",
            "alarm_strategy_names",
        ]
        read_only_fields = fields

    def get_alarm_strategy_names(self, obj):
        return sorted(obj.alarm_strategies.values_list("name", flat=True))


class AlarmStrategyQueryInputSLZ(serializers.Serializer):
    query = serializers.CharField(allow_blank=True, required=False)
    gateway_label_id = serializers.IntegerField(allow_null=True, required=False)
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
    )


class AlarmRecordSummaryQueryInputSLZ(serializers.Serializer):
    time_start = TimestampField(allow_null=True, required=False)
    time_end = TimestampField(allow_null=True, required=False)


class AlarmStrategySummaryQuerySLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    name = serializers.CharField(read_only=True)
    alarm_record_count = serializers.IntegerField(read_only=True)
    latest_alarm_record = serializers.DictField(read_only=True)


class AlarmRecordSummaryQueryOutputSLZ(serializers.Serializer):
    gateway = serializers.DictField(read_only=True)
    alarm_record_count = serializers.IntegerField(read_only=True)
    strategy_summary = serializers.ListField(child=AlarmStrategySummaryQuerySLZ(), read_only=True)
