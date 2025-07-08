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
from djangoql.admin import DjangoQLSearchMixin

from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppPermissionApply,
    AppPermissionApplyStatus,
    AppPermissionRecord,
    AppResourcePermission,
)


class AppAPIPermissionAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "bk_app_code", "gateway", "expires"]
    search_fields = ["bk_app_code", "gateway__id", "gateway__name"]
    list_filter = ["gateway", "expires"]


class AppResourcePermissionAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "bk_app_code", "gateway", "resource_id", "expires", "grant_type"]
    search_fields = ["bk_app_code", "resource_id", "gateway__id", "gateway__name"]
    list_filter = ["gateway", "expires"]


class AppPermissionApplyAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = [
        "id",
        "bk_app_code",
        "gateway",
        "grant_dimension",
        "expire_days",
        "applied_by",
        "created_time",
        "status",
    ]
    search_fields = ["bk_app_code", "gateway__id", "gateway__name", "resource__id", "resource__name"]
    list_filter = ["gateway", "grant_dimension", "status"]


class AppPermissionRecordAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = [
        "id",
        "bk_app_code",
        "gateway",
        "grant_dimension",
        "expire_days",
        "applied_by",
        "handled_by",
        "handled_time",
        "status",
    ]
    search_fields = ["bk_app_code", "gateway__id", "gateway__name"]
    list_filter = ["gateway", "grant_dimension", "status"]


class AppPermissionApplyStatusAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "bk_app_code", "apply", "resource", "status"]
    search_fields = ["bk_app_code"]
    list_filter = ["gateway", "grant_dimension", "status"]


admin.site.register(AppGatewayPermission, AppAPIPermissionAdmin)
admin.site.register(AppResourcePermission, AppResourcePermissionAdmin)
admin.site.register(AppPermissionApply, AppPermissionApplyAdmin)
admin.site.register(AppPermissionRecord, AppPermissionRecordAdmin)
admin.site.register(AppPermissionApplyStatus, AppPermissionApplyStatusAdmin)
