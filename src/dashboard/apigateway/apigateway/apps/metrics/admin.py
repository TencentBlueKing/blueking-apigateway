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
from django.contrib import admin
from django.contrib.admin import SimpleListFilter
from djangoql.admin import DjangoQLSearchMixin

# Register your models here.
from apigateway.apps.metrics.models import StatisticsAppRequestByDay, StatisticsGatewayRequestByDay
from apigateway.core.models import Gateway


class StatisticsRequestFilter(SimpleListFilter):
    title = "gateway_id"
    parameter_name = "gateway_id"

    def lookups(self, request, model_admin):
        return [(obj.id, "<Gateway: {}/{}>".format(obj.id, obj.name)) for obj in Gateway.objects.all()]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(gateway_id=self.value())
        return queryset


class StatisticsGatewayRequestByDayAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["gateway_id", "stage_name", "total_count", "failed_count", "start_time", "end_time"]
    list_filter = [StatisticsRequestFilter]


class StatisticsAppRequestByDayAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["gateway_id", "stage_name", "bk_app_code", "total_count", "failed_count", "start_time", "end_time"]
    list_filter = [StatisticsRequestFilter]


admin.site.register(StatisticsGatewayRequestByDay, StatisticsGatewayRequestByDayAdmin)
admin.site.register(StatisticsAppRequestByDay, StatisticsAppRequestByDayAdmin)
