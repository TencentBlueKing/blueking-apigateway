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

from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginForm, PluginType


class PluginTypeAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "code", "name", "is_public", "scope"]
    search_fields = ["code", "name"]
    list_filter = ["code", "is_public", "scope"]


class PluginFormAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "type", "style", "language"]
    search_fields = ["notes"]
    list_filter = ["type", "language", "style"]


class PluginConfigAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "gateway", "name", "type"]
    search_fields = ["type", "gateway__id", "gateway__name"]
    list_filter = ["type", "gateway"]


class PluginBindingAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "scope_type", "scope_id", "config", "gateway", "source"]
    search_fields = ["scope_id", "gateway__id", "gateway__name"]
    list_filter = ["scope_type", "gateway", "source"]


admin.site.register(PluginType, PluginTypeAdmin)
admin.site.register(PluginForm, PluginFormAdmin)
admin.site.register(PluginConfig, PluginConfigAdmin)
admin.site.register(PluginBinding, PluginBindingAdmin)
