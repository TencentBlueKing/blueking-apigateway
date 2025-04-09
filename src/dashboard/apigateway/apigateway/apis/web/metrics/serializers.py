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
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.apps.metrics.constants import MetricsInstantEnum, MetricsRangeEnum, MetricsRequestEnum


class MetricsQueryRangeInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(required=True, help_text="环境 id")
    resource_id = serializers.IntegerField(allow_null=True, required=False, help_text="资源 id")
    metrics = serializers.ChoiceField(choices=MetricsRangeEnum.get_choices(), help_text="metric 类型")
    time_range = serializers.IntegerField(required=False, min_value=0, help_text="时间范围")
    time_start = serializers.IntegerField(required=False, min_value=0, help_text="开始时间")
    time_end = serializers.IntegerField(required=False, min_value=0, help_text="结束时间")

    def validate(self, data):
        if not (data.get("time_start") and data.get("time_end") or data.get("time_range")):
            raise serializers.ValidationError(_("参数 time_start+time_end, time_range 必须一组有效。"))
        return data


class MetricsQueryInstantInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(required=True, help_text="环境 id")
    resource_id = serializers.IntegerField(allow_null=True, required=False, help_text="资源 id")
    metrics = serializers.ChoiceField(choices=MetricsInstantEnum.get_choices(), help_text="metric 类型")
    time_range = serializers.IntegerField(required=False, min_value=0, help_text="时间范围")
    time_start = serializers.IntegerField(required=False, min_value=0, help_text="开始时间")
    time_end = serializers.IntegerField(required=False, min_value=0, help_text="结束时间")

    def validate(self, data):
        if not (data.get("time_start") and data.get("time_end") or data.get("time_range")):
            raise serializers.ValidationError(_("参数 time_start+time_end, time_range 必须一组有效。"))
        return data


class MetricsQueryRequestInputSLZ(serializers.Serializer):
    stage_id = serializers.IntegerField(required=True, help_text="环境 id")
    resource_id = serializers.IntegerField(allow_null=True, required=False, help_text="资源 id")
    bk_app_code = serializers.CharField(allow_null=True, required=False, help_text="app code")
    time_start = serializers.IntegerField(required=False, min_value=0, help_text="开始时间")
    time_end = serializers.IntegerField(required=False, min_value=0, help_text="结束时间")
    type = serializers.ChoiceField(choices=MetricsRequestEnum.get_choices(), required=True, help_text="请求类型")

    def validate(self, data):
        if not (data.get("time_start") and data.get("time_end")):
            raise serializers.ValidationError(_("参数 time_start+time_end 必须同时有效。"))

        time_ = int((timezone.now() - relativedelta(months=6)).timestamp())
        if data["time_start"] < time_:
            raise serializers.ValidationError(_("查询时间范围不可超过半年"))
        return data
