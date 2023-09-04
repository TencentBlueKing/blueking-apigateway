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
from django.contrib import admin

from apigateway.apps.permission.models import (
    AppAPIPermission,
    AppPermissionApply,
    AppPermissionApplyStatus,
    AppPermissionRecord,
    AppResourcePermission,
)


class AppAPIPermissionAdmin(admin.ModelAdmin):
    list_display = ["id", "bk_app_code", "gateway", "expires"]
    search_fields = ["bk_app_code"]
    list_filter = ["gateway"]


class AppResourcePermissionAdmin(admin.ModelAdmin):
    list_display = ["id", "bk_app_code", "gateway", "resource_id", "expires", "grant_type"]
    search_fields = ["bk_app_code", "resource_id"]
    list_filter = ["gateway"]


class AppPermissionApplyAdmin(admin.ModelAdmin):
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
    search_fields = ["bk_app_code"]
    list_filter = ["gateway"]


class AppPermissionRecordAdmin(admin.ModelAdmin):
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
    search_fields = ["bk_app_code"]
    list_filter = ["gateway", "status"]


class AppPermissionApplyStatusAdmin(admin.ModelAdmin):
    list_display = ["id", "bk_app_code", "apply", "resource", "status"]
    search_fields = ["bk_app_code"]
    list_filter = ["gateway", "status"]


admin.site.register(AppAPIPermission, AppAPIPermissionAdmin)
admin.site.register(AppResourcePermission, AppResourcePermissionAdmin)
admin.site.register(AppPermissionApply, AppPermissionApplyAdmin)
admin.site.register(AppPermissionRecord, AppPermissionRecordAdmin)
admin.site.register(AppPermissionApplyStatus, AppPermissionApplyStatusAdmin)
