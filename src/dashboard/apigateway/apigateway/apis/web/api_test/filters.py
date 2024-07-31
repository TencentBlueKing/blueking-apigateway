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
from datetime import datetime

from django_filters import rest_framework as filters

from apigateway.apps.api_debug.models import APIDebugHistory


class APIDebugHistoryRecordFilter(filters.FilterSet):
    time_start = filters.NumberFilter(method="time_start_filter")
    time_end = filters.NumberFilter(method="time_end_filter")
    resource_name = filters.CharFilter(field_name="resource_name", lookup_expr="icontains")

    class Meta:
        model = APIDebugHistory
        fields = [
            "created_time",
            "time_start",
            "time_end",
            "resource_name",
        ]

    def time_start_filter(self, queryset, name, value):
        value = int(value)
        return queryset.filter(created_time__gte=datetime.fromtimestamp(value))

    def time_end_filter(self, queryset, name, value):
        value = int(value)
        return queryset.filter(created_time__lt=datetime.fromtimestamp(value))
