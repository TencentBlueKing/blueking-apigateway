# -*- coding: utf-8 -*-
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
from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase

from apigateway.apps.api_debug.admin import APIDebugHistoryAdmin
from apigateway.apps.api_debug.models import APIDebugHistory
from apigateway.apps.data_plane.admin import GatewayDataPlaneBindingAdmin
from apigateway.apps.data_plane.models import GatewayDataPlaneBinding
from apigateway.apps.mcp_server.admin import MCPServerAdmin, MCPServerCategoryAdmin
from apigateway.apps.mcp_server.models import MCPServer, MCPServerCategory
from apigateway.apps.permission.admin import AppPermissionApplyAdmin
from apigateway.apps.permission.models import AppPermissionApply
from apigateway.apps.support.admin import ResourceDocAdmin
from apigateway.apps.support.models import ResourceDoc
from apigateway.core.admin import GatewayAdmin
from apigateway.core.models import Gateway


class TestAuditFieldsDisplayAdminMixin(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin_site = AdminSite()
        cls.request = RequestFactory().get("/")

    def test_gateway_admin_appends_audit_fields(self):
        model_admin = GatewayAdmin(Gateway, self.admin_site)

        self.assertEqual(
            model_admin.get_fields(self.request)[-4:],
            ["created_by", "updated_by", "created_time", "updated_time"],
        )
        self.assertEqual(
            model_admin.get_readonly_fields(self.request),
            ["created_time", "updated_time"],
        )

    def test_mcp_server_admin_appends_audit_fieldset(self):
        model_admin = MCPServerAdmin(MCPServer, self.admin_site)
        self.assertEqual(
            model_admin.get_fieldsets(self.request)[-1],
            ("Audit", {"fields": ("created_by", "updated_by", "created_time", "updated_time")}),
        )

    def test_mcp_server_category_admin_preserves_custom_readonly_fields(self):
        model_admin = MCPServerCategoryAdmin(MCPServerCategory, self.admin_site)
        special_category = type("SpecialCategory", (), {"is_special_category": True})()

        self.assertEqual(
            model_admin.get_readonly_fields(self.request, obj=special_category),
            ["created_time", "updated_time", "name"],
        )
        self.assertEqual(
            model_admin.get_fieldsets(self.request)[-1],
            ("Audit", {"fields": ("created_by", "updated_by", "created_time", "updated_time")}),
        )

    def test_resource_doc_admin_appends_audit_fields(self):
        model_admin = ResourceDocAdmin(ResourceDoc, self.admin_site)

        self.assertEqual(
            model_admin.get_fields(self.request)[-4:],
            ["created_by", "updated_by", "created_time", "updated_time"],
        )

    def test_api_debug_history_admin_appends_audit_fields(self):
        model_admin = APIDebugHistoryAdmin(APIDebugHistory, self.admin_site)

        self.assertEqual(
            model_admin.get_fields(self.request)[-4:],
            ["created_by", "updated_by", "created_time", "updated_time"],
        )

    def test_permission_apply_admin_only_appends_existing_audit_fields(self):
        model_admin = AppPermissionApplyAdmin(AppPermissionApply, self.admin_site)

        self.assertEqual(model_admin.get_fields(self.request)[-2:], ["created_time", "updated_time"])
        self.assertEqual(model_admin.get_readonly_fields(self.request), ["created_time", "updated_time"])

    def test_gateway_data_plane_binding_admin_preserves_existing_readonly_fields(self):
        model_admin = GatewayDataPlaneBindingAdmin(GatewayDataPlaneBinding, self.admin_site)

        self.assertEqual(model_admin.get_readonly_fields(self.request), ["created_time", "updated_time"])
        self.assertEqual(
            model_admin.get_fields(self.request)[-4:],
            ["created_by", "updated_by", "created_time", "updated_time"],
        )
