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

from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerCategory,
)


class MCPServerCategoryAdmin(DjangoQLSearchMixin, admin.ModelAdmin):
    """MCPServer 分类管理"""

    djangoql_completion_enabled_by_default = False
    list_display = [
        "id",
        "name",
        "display_name",
        "type",
        "is_active",
        "sort_order",
        "created_time",
        "updated_time",
    ]
    search_fields = ["name", "display_name", "description"]
    list_filter = ["type", "is_active"]
    list_editable = ["sort_order", "is_active"]
    ordering = ["sort_order", "id"]

    fieldsets = (
        (None, {"fields": ("name", "display_name", "description", "type")}),
        ("状态和排序", {"fields": ("is_active", "sort_order")}),
    )

    def get_readonly_fields(self, request, obj=None):
        """官方和精选分类的类型不允许修改"""
        readonly_fields = ["created_time", "updated_time"]
        if obj and obj.is_special_category:
            readonly_fields.append("type")
        return readonly_fields


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
        "get_categories_display",
        "created_by",
        "created_time",
        "updated_time",
    ]
    search_fields = ["id", "name", "title", "gateway__name", "_labels"]
    list_filter = ["gateway", "is_public", "status", "categories"]
    filter_horizontal = ["categories"]

    fieldsets = (
        (None, {"fields": ("name", "title", "description", "gateway", "stage")}),
        ("状态和权限", {"fields": ("status", "is_public", "protocol_type")}),
        ("分类", {"fields": ("categories",)}),
        ("资源配置", {"fields": ("_labels", "_resource_names"), "classes": ("collapse",)}),
    )

    def get_categories_display(self, obj):
        """显示分类列表"""
        categories = obj.categories.filter(is_active=True)
        if categories.exists():
            return ", ".join([cat.display_name for cat in categories])
        return "-"

    get_categories_display.short_description = "分类"  # type: ignore

    def get_queryset(self, request):
        """优化查询"""
        return super().get_queryset(request).prefetch_related("categories")


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


admin.site.register(MCPServerCategory, MCPServerCategoryAdmin)
admin.site.register(MCPServer, MCPServerAdmin)
admin.site.register(MCPServerAppPermission, MCPServerAppPermissionAdmin)
admin.site.register(MCPServerAppPermissionApply, MCPServerAppPermissionApplyAdmin)
