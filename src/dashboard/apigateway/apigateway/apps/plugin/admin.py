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

from apigateway.apps.plugin.models import Plugin, PluginBinding, PluginConfig, PluginForm, PluginType


class PluginTypeAdmin(admin.ModelAdmin):
    list_display = ["id", "code", "name_i18n"]
    search_fields = ["code", "name_i18n"]
    list_filter = ["code", "is_public"]


class PluginFormAdmin(admin.ModelAdmin):
    list_display = ["id", "type", "language"]
    search_fields = ["notes"]
    list_filter = ["type", "language"]


class PluginConfigAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "api"]
    search_fields = ["name"]
    list_filter = ["type", "api"]


class PluginBindingAdmin(admin.ModelAdmin):
    list_display = ["id", "scope_type", "scope_id", "config", "api"]
    search_fields = ["scope_id"]
    list_filter = ["scope_type", "api"]


class LegacyPluginAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "api"]
    search_fields = ["name"]
    list_filter = ["type", "api"]


admin.site.register(Plugin, LegacyPluginAdmin)
admin.site.register(PluginType, PluginTypeAdmin)
admin.site.register(PluginForm, PluginFormAdmin)
admin.site.register(PluginConfig, PluginConfigAdmin)
admin.site.register(PluginBinding, PluginBindingAdmin)
