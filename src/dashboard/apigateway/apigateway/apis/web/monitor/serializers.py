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

from apigateway.apps.monitor.constants import DETECT_METHOD_CHOICES, AlarmStatusEnum, NoticeRoleEnum, NoticeWayEnum
from apigateway.apps.monitor.models import AlarmRecord, AlarmStrategy
from apigateway.biz.gateway_label import GatewayLabelHandler
from apigateway.common.fields import CurrentGatewayDefault, TimestampField
from apigateway.core.models import Stage


class DetectConfigSLZ(serializers.Serializer):
    duration = serializers.IntegerField(min_value=1, help_text="持续时间")
    method = serializers.ChoiceField(choices=DETECT_METHOD_CHOICES, help_text="检测方法")
    count = serializers.IntegerField(min_value=0, help_text="次数")


class ConvergeConfigSLZ(serializers.Serializer):
    duration = serializers.IntegerField(min_value=0, help_text="持续时间")


class NoticeConfigSLZ(serializers.Serializer):
    notice_way = serializers.ListField(
        child=serializers.ChoiceField(choices=NoticeWayEnum.get_choices()),
        help_text="通知方式",
    )
    notice_role = serializers.ListField(
        child=serializers.ChoiceField(choices=NoticeRoleEnum.get_choices()),
        allow_empty=True,
        help_text="通知组",
    )
    notice_extra_receiver = serializers.ListField(
        child=serializers.CharField(),
        allow_empty=True,
        help_text="其他通知对象",
    )

    def validate(self, data):
        if not (data.get("notice_role") or data.get("notice_extra_receiver")):
            raise serializers.ValidationError(_("通知对象、其他通知对象不能同时为空。"))
        return data


class AlarmStrategyConfigSLZ(serializers.Serializer):
    detect_config = DetectConfigSLZ(help_text="检测配置")
    converge_config = ConvergeConfigSLZ(help_text="收敛配置")
    notice_config = NoticeConfigSLZ(help_text="通知配置")


class AlarmStrategyInputSLZ(serializers.ModelSerializer):
    gateway = serializers.HiddenField(default=CurrentGatewayDefault(), help_text="网关")
    gateway_label_ids = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True, help_text="网关标签 id 列表"
    )
    config = AlarmStrategyConfigSLZ(help_text="告警策略配置")

    effective_stages = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True, help_text="生效环境列表"
    )

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
            "effective_stages",
        ]
        lookup_field = "id"

    def validate_config(self, value):
        # does not support writable nested fields by default
        return json.dumps(value)

    def validate_gateway_label_ids(self, value):
        gateway = self.context["request"].gateway
        not_exist_ids = set(value) - set(GatewayLabelHandler.get_valid_ids(gateway.id, value))
        if not_exist_ids:
            raise serializers.ValidationError(_("标签不存在，id={ids}").format(ids=", ".join(map(str, not_exist_ids))))

        return value

    def validate_effective_stages(self, value):
        if not isinstance(value, list):
            raise serializers.ValidationError(_("生效环境列表必须为列表"))

        if not value:
            return []

        # check if all the stages are valid
        gateway = self.context["request"].gateway
        stage_names = Stage.objects.filter(name__in=value, gateway=gateway).values_list("name", flat=True)
        if len(stage_names) != len(value):
            raise serializers.ValidationError(_("生效环境列表中存在无效的环境"))

        return value


class AlarmStrategyListOutputSLZ(serializers.ModelSerializer):
    gateway_labels = serializers.SerializerMethodField(help_text="网关标签列表")

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
            "effective_stages",
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
    time_start = TimestampField(allow_null=True, required=False, help_text="开始时间")
    time_end = TimestampField(allow_null=True, required=False, help_text="结束时间")
    alarm_strategy_id = serializers.IntegerField(allow_null=True, required=False, help_text="告警策略 id")
    status = serializers.ChoiceField(
        choices=AlarmStatusEnum.get_choices(), allow_blank=True, required=False, help_text="告警状态"
    )


class AlarmRecordQueryOutputSLZ(serializers.ModelSerializer):
    alarm_strategy_names = serializers.SerializerMethodField(help_text="告警策略名称列表")

    class Meta:
        model = AlarmRecord
        fields = [
            "id",
            "alarm_id",
            "status",
            "message",
            "created_time",
            "alarm_strategy_names",
            "comment",
        ]
        read_only_fields = fields

    def get_alarm_strategy_names(self, obj):
        return sorted(obj.alarm_strategies.values_list("name", flat=True))


class AlarmStrategyQueryInputSLZ(serializers.Serializer):
    keyword = serializers.CharField(allow_blank=True, required=False, help_text="查询关键字")
    gateway_label_id = serializers.IntegerField(allow_null=True, required=False, help_text="网关标签 id")
    order_by = serializers.ChoiceField(
        choices=["name", "-name", "updated_time", "-updated_time"],
        allow_blank=True,
        required=False,
        help_text="排序字段",
    )


class AlarmRecordSummaryQueryInputSLZ(serializers.Serializer):
    time_start = TimestampField(allow_null=True, required=False, help_text="开始时间")
    time_end = TimestampField(allow_null=True, required=False, help_text="结束时间")


class AlarmStrategySummaryQuerySLZ(serializers.Serializer):
    id = serializers.IntegerField(read_only=True, help_text="策略 id")
    name = serializers.CharField(read_only=True, help_text="策略名称")
    alarm_record_count = serializers.IntegerField(read_only=True, help_text="告警记录总数")
    latest_alarm_record = serializers.DictField(read_only=True, help_text="最新告警记录")


class AlarmRecordSummaryQueryOutputSLZ(serializers.Serializer):
    gateway = serializers.DictField(read_only=True, help_text="网关")
    alarm_record_count = serializers.IntegerField(read_only=True, help_text="告警记录总数")
    strategy_summary = serializers.ListField(
        child=AlarmStrategySummaryQuerySLZ(), read_only=True, help_text="策略汇总"
    )
