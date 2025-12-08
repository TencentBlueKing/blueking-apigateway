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

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerAppPermissionApply


class MCPServerAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = [
        "id",
        "name",
        "title",
        "gateway",
        "stage",
        "is_public",
        "status",
        "created_by",
        "created_time",
        "updated_time",
    ]
    search_fields = ["id", "name", "title", "gateway__name", "_labels"]
    list_filter = ["gateway", "is_public", "status"]


class MCPServerAppPermissionAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = ["id", "bk_app_code", "mcp_server", "expires", "grant_type", "created_time", "updated_time"]
    search_fields = ["bk_app_code", "mcp_server__name"]
    list_filter = ["mcp_server", "grant_type"]


class MCPServerAppPermissionApplyAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    djangoql_completion_enabled_by_default = False
    list_display = [
        "id",
        "bk_app_code",
        "mcp_server",
        "applied_by",
        "applied_time",
        "handled_by",
        "handled_time",
        "status",
        "created_time",
        "updated_time",
    ]
    search_fields = ["bk_app_code", "mcp_server__name", "applied_by"]
    list_filter = ["mcp_server", "status"]


admin.site.register(MCPServer, MCPServerAdmin)
admin.site.register(MCPServerAppPermission, MCPServerAppPermissionAdmin)
admin.site.register(MCPServerAppPermissionApply, MCPServerAppPermissionApplyAdmin)
