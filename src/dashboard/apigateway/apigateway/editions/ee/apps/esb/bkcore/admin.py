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
from djangoql.admin import DjangoQLSearchMixin

from apigateway.apps.esb.bkcore import models


class ComponentSystemAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "name", "description", "timeout", "board"]
    search_fields = ["id", "name", "description"]
    list_filter = ["board"]
    readonly_fields = ["board", "data_type"]


class ESBChannelAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "system", "name", "method", "path", "is_active", "board"]
    search_fields = ["id", "name", "path"]
    list_fields = ["board"]
    list_filter = ["system"]
    readonly_fields = ["board", "data_type"]


class ESBChannelExtendAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["component_id", "component", "board"]
    search_fields = ["component_id"]
    list_fields = ["board"]
    readonly_fields = ["board"]


class AppComponentPermissionAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["bk_app_code", "component_id", "expires", "board"]
    search_fields = ["bk_app_code", "component_id"]
    list_filter = ["board"]
    readonly_fields = ["board"]


class ComponentDocAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["component_id", "board"]
    search_fields = ["component_id"]
    list_filter = ["board"]
    readonly_fields = ["board"]


class DocCategoryAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "name", "priority", "board"]
    search_fields = ["name"]
    list_filter = ["board"]
    readonly_fields = ["board", "data_type"]


class SystemDocCategoryAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["system", "doc_category", "board"]
    search_fields = ["system__id", "doc_category__id"]
    list_filter = ["board"]
    readonly_fields = ["board"]


class AppPermissionApplyRecordAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["bk_app_code", "system", "applied_by", "applied_time", "handled_by", "handled_time", "status"]
    search_fields = ["bk_app_code", "applied_by"]
    list_filter = ["bk_app_code"]
    readonly_fields = ["board"]


class FunctionControllerAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["func_code", "func_name", "switch_status", "board"]
    search_fields = ["func_code", "func_name"]
    list_filter = ["board"]
    readonly_fields = ["board"]


class AppAccountAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["app_code", "app_token", "created_time"]
    search_fields = ["app_code"]


class WxmpAccessTokenAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["wx_app_id", "access_token", "expires"]
    search_fields = ["wx_app_id"]


class ComponentResourceBindingAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["component_id", "component_method", "component_path", "resource_id"]
    search_fields = ["component_id", "resource_id", "component_path"]
    readonly_fields = ["board"]


class ComponentReleaseHistoryAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["resource_version_id", "status", "created_by", "created_time"]
    search_fields = ["resource_version_id"]
    list_filter = ["status"]
    exclude = ["data"]
    readonly_fields = ["board"]


admin.site.register(models.ComponentSystem, ComponentSystemAdmin)
admin.site.register(models.ESBChannel, ESBChannelAdmin)
admin.site.register(models.ESBChannelExtend, ESBChannelExtendAdmin)
admin.site.register(models.AppComponentPermission, AppComponentPermissionAdmin)
admin.site.register(models.ComponentDoc, ComponentDocAdmin)
admin.site.register(models.DocCategory, DocCategoryAdmin)
admin.site.register(models.SystemDocCategory, SystemDocCategoryAdmin)
admin.site.register(models.AppPermissionApplyRecord, AppPermissionApplyRecordAdmin)
admin.site.register(models.FunctionController, FunctionControllerAdmin)
admin.site.register(models.AppAccount, AppAccountAdmin)
admin.site.register(models.WxmpAccessToken, WxmpAccessTokenAdmin)
admin.site.register(models.ComponentResourceBinding, ComponentResourceBindingAdmin)
admin.site.register(models.ComponentReleaseHistory, ComponentReleaseHistoryAdmin)
