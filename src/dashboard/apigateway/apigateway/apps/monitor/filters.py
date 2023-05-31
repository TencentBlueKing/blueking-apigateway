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
from rest_framework.filters import BaseFilterBackend

from apigateway.apps.monitor.models import AlarmStrategy
from apigateway.apps.monitor.serializers import AlarmRecordQuerySLZ


class AlarmRecordFilterBackend(BaseFilterBackend):
    """AlarmRecord filter"""

    def filter_queryset(self, request, queryset, view):
        slz = AlarmRecordQuerySLZ(data=request.query_params)
        slz.is_valid(raise_exception=True)

        data = slz.validated_data

        strategy_queryset = AlarmStrategy.objects.filter(api=request.gateway)

        if data.get("alarm_strategy_id"):
            strategy_queryset = strategy_queryset.filter(id=data["alarm_strategy_id"])

        queryset = queryset.filter(alarm_strategies__in=strategy_queryset)

        if data.get("status"):
            queryset = queryset.filter(status=data["status"])

        if data.get("time_start") and data.get("time_end"):
            queryset = queryset.filter(created_time__range=(data["time_start"], data["time_end"]))

        return queryset.distinct()
