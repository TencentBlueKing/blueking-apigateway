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
from django.utils.translation import gettext as _
from rest_framework import serializers

from apigateway.utils.time import MetricsSmartTimeRange

MAX_METRICS_TIME_RANGE_SECONDS = 180 * 24 * 60 * 60


class MetricsTimeRangeValidator:
    """Validate the effective metrics interval, preserving explicit timestamp priority."""

    def __call__(self, data):
        if not (data.get("time_start") and data.get("time_end") or data.get("time_range")):
            raise serializers.ValidationError(_("参数 time_start+time_end, time_range 必须一组有效。"))

        time_start, time_end = MetricsSmartTimeRange(
            data.get("time_start"), data.get("time_end"), data.get("time_range")
        ).get_head_and_tail()
        if time_start > time_end:
            raise serializers.ValidationError(_("参数 time_start 不能晚于 time_end。"))
        if time_end - time_start > MAX_METRICS_TIME_RANGE_SECONDS:
            raise serializers.ValidationError(_("查询时间范围不可超过 180 天。"))
