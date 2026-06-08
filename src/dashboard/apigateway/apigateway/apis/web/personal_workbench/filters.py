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

from django.db.models import Q
from django_filters import rest_framework as filters
from rest_framework.exceptions import ValidationError

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import ApplyStatusEnum, GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord
from apigateway.utils.time import utctime


class TimeRangeFilterMixin:
    def filter_queryset(self, queryset):
        time_start = self.form.cleaned_data.get("time_start")
        time_end = self.form.cleaned_data.get("time_end")
        if time_start is not None and time_end is not None and time_start > time_end:
            raise ValidationError({"time_end": "time_end 必须大于等于 time_start"})

        return super().filter_queryset(queryset)


class CreatedTimeRangeFilterMixin(TimeRangeFilterMixin):
    def filter_created_time_start(self, queryset, name, value):
        return queryset.filter(created_time__gte=utctime(int(value)).datetime)

    def filter_created_time_end(self, queryset, name, value):
        return queryset.filter(created_time__lte=utctime(int(value)).datetime)


class AppliedTimeRangeFilterMixin(TimeRangeFilterMixin):
    def filter_applied_time_start(self, queryset, name, value):
        return queryset.filter(applied_time__gte=utctime(int(value)).datetime)

    def filter_applied_time_end(self, queryset, name, value):
        return queryset.filter(applied_time__lte=utctime(int(value)).datetime)


class KeywordFilterMixin:
    def keyword_filter(self, queryset, name, value):
        return queryset.filter(Q(bk_app_code__icontains=value) | Q(gateway__name__icontains=value))


class MCPKeywordFilterMixin:
    def keyword_filter(self, queryset, name, value):
        return queryset.filter(
            Q(bk_app_code__icontains=value)
            | Q(mcp_server__name__icontains=value)
            | Q(mcp_server__title__icontains=value)
        )


class WorkbenchGatewayPermissionApplyFilter(CreatedTimeRangeFilterMixin, KeywordFilterMixin, filters.FilterSet):
    """个人工作台 - API 网关权限申请筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    gateway_id = filters.NumberFilter(field_name="gateway_id")
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())
    status = filters.ChoiceFilter(choices=ApplyStatusEnum.get_choices())
    time_start = filters.NumberFilter(method="filter_created_time_start")
    time_end = filters.NumberFilter(method="filter_created_time_end")
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = AppPermissionApply
        fields = [
            "bk_app_code",
            "applied_by",
            "gateway_id",
            "grant_dimension",
            "status",
            "time_start",
            "time_end",
            "keyword",
        ]


class WorkbenchGatewayPendingPermissionApplyFilter(CreatedTimeRangeFilterMixin, KeywordFilterMixin, filters.FilterSet):
    """个人工作台 - API 网关待办权限申请筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    gateway_id = filters.NumberFilter(field_name="gateway_id")
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())
    time_start = filters.NumberFilter(method="filter_created_time_start")
    time_end = filters.NumberFilter(method="filter_created_time_end")
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = AppPermissionApply
        fields = [
            "bk_app_code",
            "applied_by",
            "gateway_id",
            "grant_dimension",
            "time_start",
            "time_end",
            "keyword",
        ]


class WorkbenchGatewayPermissionRecordFilter(AppliedTimeRangeFilterMixin, KeywordFilterMixin, filters.FilterSet):
    """个人工作台 - API 网关已办记录筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    gateway_id = filters.NumberFilter(field_name="gateway_id")
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())
    status = filters.ChoiceFilter(choices=ApplyStatusEnum.get_choices())
    time_start = filters.NumberFilter(method="filter_applied_time_start")
    time_end = filters.NumberFilter(method="filter_applied_time_end")
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = AppPermissionRecord
        fields = [
            "bk_app_code",
            "applied_by",
            "gateway_id",
            "grant_dimension",
            "status",
            "time_start",
            "time_end",
            "keyword",
        ]


class WorkbenchMCPPendingPermissionApplyFilter(AppliedTimeRangeFilterMixin, MCPKeywordFilterMixin, filters.FilterSet):
    """个人工作台 - MCP Server 待办权限申请筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    gateway_id = filters.NumberFilter(field_name="mcp_server__gateway_id")
    mcp_server_id = filters.NumberFilter(field_name="mcp_server_id")
    time_start = filters.NumberFilter(method="filter_applied_time_start")
    time_end = filters.NumberFilter(method="filter_applied_time_end")
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = MCPServerAppPermissionApply
        fields = [
            "bk_app_code",
            "applied_by",
            "gateway_id",
            "mcp_server_id",
            "time_start",
            "time_end",
            "keyword",
        ]


class WorkbenchMCPPermissionApplyFilter(AppliedTimeRangeFilterMixin, MCPKeywordFilterMixin, filters.FilterSet):
    """个人工作台 - MCP Server 权限申请筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    gateway_id = filters.NumberFilter(field_name="mcp_server__gateway_id")
    mcp_server_id = filters.NumberFilter(field_name="mcp_server_id")
    status = filters.ChoiceFilter(choices=MCPServerAppPermissionApplyStatusEnum.get_choices())
    time_start = filters.NumberFilter(method="filter_applied_time_start")
    time_end = filters.NumberFilter(method="filter_applied_time_end")
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = MCPServerAppPermissionApply
        fields = [
            "bk_app_code",
            "applied_by",
            "gateway_id",
            "mcp_server_id",
            "status",
            "time_start",
            "time_end",
            "keyword",
        ]
