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

from django.db.models import Q
from django_filters import rest_framework as filters

from apigateway.apps.mcp_server.constants import MCPServerAppPermissionApplyStatusEnum
from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.constants import GrantDimensionEnum
from apigateway.apps.permission.models import AppPermissionApply, AppPermissionRecord


class WorkbenchGatewayPermissionApplyFilter(filters.FilterSet):
    """个人工作台 - API 网关权限申请筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = AppPermissionApply
        fields = ["bk_app_code", "applied_by", "grant_dimension", "keyword"]

    def keyword_filter(self, queryset, name, value):
        return queryset.filter(Q(bk_app_code__icontains=value) | Q(gateway__name__icontains=value))


class WorkbenchGatewayPermissionRecordFilter(filters.FilterSet):
    """个人工作台 - API 网关已办记录筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    grant_dimension = filters.ChoiceFilter(choices=GrantDimensionEnum.get_choices())
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = AppPermissionRecord
        fields = ["bk_app_code", "applied_by", "grant_dimension", "keyword"]

    def keyword_filter(self, queryset, name, value):
        return queryset.filter(Q(bk_app_code__icontains=value) | Q(gateway__name__icontains=value))


class WorkbenchMCPPermissionApplyFilter(filters.FilterSet):
    """个人工作台 - MCP Server 权限申请筛选器"""

    bk_app_code = filters.CharFilter(lookup_expr="icontains")
    applied_by = filters.CharFilter(lookup_expr="icontains")
    status = filters.ChoiceFilter(choices=MCPServerAppPermissionApplyStatusEnum.get_choices())
    keyword = filters.CharFilter(method="keyword_filter")

    class Meta:
        model = MCPServerAppPermissionApply
        fields = ["bk_app_code", "applied_by", "status", "keyword"]

    def keyword_filter(self, queryset, name, value):
        return queryset.filter(
            Q(bk_app_code__icontains=value)
            | Q(mcp_server__name__icontains=value)
            | Q(mcp_server__title__icontains=value)
        )
