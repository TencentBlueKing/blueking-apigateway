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
from datetime import datetime

from django_filters import rest_framework as filters

from apigateway.apps.permission.constants import GrantDimensionEnum, GrantTypeEnum
from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppPermissionRecord,
    AppResourcePermission,
)


class AppResourcePermissionFilter(filters.FilterSet):
    bk_app_code = filters.CharFilter()
    keyword = filters.CharFilter(method="query_filter")
    grant_type = filters.ChoiceFilter(choices=GrantTypeEnum.get_choices())
    resource_id = filters.NumberFilter()
    order_by = filters.OrderingFilter(
        choices=[(field, field) for field in ["bk_app_code", "-bk_app_code", "expires", "-expires"]]
    )

    class Meta:
        model = AppResourcePermission
        fields = [
            "bk_app_code",
            "keyword",
            "grant_type",
            "resource_id",
            "order_by",
        ]

    def query_filter(self, queryset, name, value):
        return queryset.filter(bk_app_code__icontains=value)


class AppPermissionApplyFilter(filters.FilterSet):
    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())

    class Meta:
        model = AppPermissionApply
        fields = [
            "bk_app_code",
            "applied_by",
            "grant_dimension",
        ]


class AppGatewayPermissionFilter(filters.FilterSet):
    bk_app_code = filters.CharFilter()
    keyword = filters.CharFilter(method="query_filter")
    order_by = filters.OrderingFilter(
        choices=[(field, field) for field in ["bk_app_code", "-bk_app_code", "expires", "-expires"]]
    )

    class Meta:
        model = AppGatewayPermission
        fields = [
            "bk_app_code",
            "keyword",
            "order_by",
        ]

    def query_filter(self, queryset, name, value):
        return queryset.filter(bk_app_code__icontains=value)


class AppPermissionRecordFilter(filters.FilterSet):
    time_start = filters.NumberFilter(method="time_start_filter")
    time_end = filters.NumberFilter(method="time_end_filter")
    bk_app_code = filters.CharFilter()
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())

    class Meta:
        model = AppPermissionRecord
        fields = [
            "time_start",
            "time_end",
            "bk_app_code",
            "grant_dimension",
        ]

    def time_start_filter(self, queryset, name, value):
        return queryset.filter(handled_time__gte=datetime.fromtimestamp(value))

    def time_end_filter(self, queryset, name, value):
        return queryset.filter(handled_time__lt=datetime.fromtimestamp(value))
