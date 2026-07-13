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

import datetime
from unittest.mock import patch

import pytest
from ddf import G

from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppResourcePermission,
)
from apigateway.biz.permission import (
    AppPermissionBuilder,
    ResourcePermissionHandler,
    build_resource_permission_display,
)
from apigateway.common.tenant.constants import (
    TENANT_ID_OPERATION,
    TenantModeEnum,
)
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestResourcePermissionHandler:
    def test_grant_or_renewal_expire_soon(self, fake_gateway, fake_resource):
        data = [
            {
                "gateway": fake_gateway,
                "resource_id": fake_resource.id,
                "bk_app_code": "test",
            },
        ]
        for test in data:
            handler = ResourcePermissionHandler()
            handler.grant_or_renewal_expire_soon(test["gateway"], test["resource_id"], test["bk_app_code"], 1, 300)
            app_resource_permission = AppResourcePermission.objects.get_permission_or_none(
                gateway=test["gateway"],
                resource_id=test["resource_id"],
                bk_app_code=test["bk_app_code"],
            )
            assert not app_resource_permission.has_expired

    def test_sync_from_gateway_permission(self):
        bk_app_code = "test"
        gateway = G(Gateway)
        resource = G(Resource, gateway=gateway)

        # has no api-perm
        handler = ResourcePermissionHandler()
        handler.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert AppResourcePermission.objects.filter(gateway=gateway, bk_app_code=bk_app_code).count() == 0

        # api-perm expired
        api_perm = G(
            AppGatewayPermission,
            gateway=gateway,
            bk_app_code=bk_app_code,
            expires=now_datetime() - datetime.timedelta(seconds=10),
        )
        ResourcePermissionHandler.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert AppResourcePermission.objects.filter(gateway=gateway, bk_app_code=bk_app_code).count() == 1

        # api-perm unexpired
        api_perm.expires = now_datetime() + datetime.timedelta(seconds=10)
        api_perm.save()
        ResourcePermissionHandler.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert AppResourcePermission.objects.filter(gateway=gateway, bk_app_code=bk_app_code).count() == 1


def test_build_permission_display_preserves_gateway_name(fake_gateway):
    item = build_resource_permission_display(
        resource_id=1,
        resource_name="get_user",
        gateway_id=fake_gateway.id,
        gateway_name=fake_gateway.name,
        description="desc",
        description_en="desc en",
        resource_perm_required=True,
        doc_link="",
        gateway_permission=None,
        resource_permission=None,
        gateway_permission_apply_status="",
        resource_permission_apply_status="",
    )

    assert item["gateway_name"] == fake_gateway.name
    assert item["name"] == "get_user"


def test_app_permission_builder_uses_released_resource_version_data(fake_gateway, fake_resource_version, fake_release):
    G(AppGatewayPermission, gateway=fake_gateway, bk_app_code="test", expires=None)

    result = AppPermissionBuilder("test").build()

    expected_resource_ids = {item["id"] for item in fake_resource_version.data if item["is_public"]}
    assert {item["id"] for item in result} == expected_resource_ids


class TestConvertAppliedByToDisplayName:
    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", False)
    def test_multi_tenant_mode_disabled(self):
        """When multi-tenant mode is disabled, should return applied_by unchanged"""
        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "admin"

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    def test_same_tenant_mode_and_id(self, mock_get_app_tenant_info):
        """When app and gateway have same tenant mode and id, should return applied_by unchanged"""
        mock_get_app_tenant_info.return_value = ("global", "tenant-1")

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "admin"
        mock_get_app_tenant_info.assert_called_once_with("test-app")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    @patch("apigateway.biz.permission.permission.query_display_names_cached")
    def test_force_convert_same_tenant(self, mock_query_display_names, mock_get_app_tenant_info):
        """When force_convert is True, should convert display name even in same tenant"""
        mock_get_app_tenant_info.return_value = ("global", "tenant-1")
        mock_query_display_names.return_value = [{"display_name": "Admin User"}]

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
            force_convert=True,
        )
        assert result == "Admin User"
        mock_get_app_tenant_info.assert_called_once_with("test-app")
        mock_query_display_names.assert_called_once_with(TENANT_ID_OPERATION, "admin")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    @patch("apigateway.biz.permission.permission.query_display_names_cached")
    def test_different_tenant_with_display_name_found(self, mock_query_display_names, mock_get_app_tenant_info):
        """When tenants are different and display name is found, should return the display name"""
        mock_get_app_tenant_info.return_value = ("private", "tenant-2")
        mock_query_display_names.return_value = [{"display_name": "Admin User"}]

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "Admin User"
        mock_get_app_tenant_info.assert_called_once_with("test-app")
        mock_query_display_names.assert_called_once_with("tenant-2", "admin")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    @patch("apigateway.biz.permission.permission.query_display_names_cached")
    def test_different_tenant_with_display_name_without_key(self, mock_query_display_names, mock_get_app_tenant_info):
        """When display name dict doesn't have display_name key, should return applied_by"""
        mock_get_app_tenant_info.return_value = ("private", "tenant-2")
        mock_query_display_names.return_value = [{"username": "admin"}]

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "admin"
        mock_get_app_tenant_info.assert_called_once_with("test-app")
        mock_query_display_names.assert_called_once_with("tenant-2", "admin")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    @patch("apigateway.biz.permission.permission.query_display_names_cached")
    def test_different_tenant_with_empty_display_names(self, mock_query_display_names, mock_get_app_tenant_info):
        """When display names list is empty, should return applied_by"""
        mock_get_app_tenant_info.return_value = ("private", "tenant-2")
        mock_query_display_names.return_value = []

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "admin"
        mock_get_app_tenant_info.assert_called_once_with("test-app")
        mock_query_display_names.assert_called_once_with("tenant-2", "admin")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    @patch("apigateway.biz.permission.permission.query_display_names_cached")
    def test_app_tenant_is_global(self, mock_query_display_names, mock_get_app_tenant_info):
        """When app tenant mode is GLOBAL, should use TENANT_ID_OPERATION"""
        mock_get_app_tenant_info.return_value = (TenantModeEnum.GLOBAL.value, "original-tenant-id")
        mock_query_display_names.return_value = [{"display_name": "Global Admin"}]

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="private",
            gateway_tenant_id="tenant-1",
        )
        assert result == "Global Admin"
        mock_get_app_tenant_info.assert_called_once_with("test-app")
        mock_query_display_names.assert_called_once_with(TENANT_ID_OPERATION, "admin")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    def test_exception_during_tenant_info_retrieval(self, mock_get_app_tenant_info):
        """When an exception occurs during tenant info retrieval, should return applied_by"""
        mock_get_app_tenant_info.side_effect = Exception("Connection error")

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "admin"
        mock_get_app_tenant_info.assert_called_once_with("test-app")

    @patch("apigateway.biz.permission.permission.settings.ENABLE_MULTI_TENANT_MODE", True)
    @patch("apigateway.biz.permission.permission.get_app_tenant_info_cached")
    @patch("apigateway.biz.permission.permission.query_display_names_cached")
    def test_exception_during_display_name_query(self, mock_query_display_names, mock_get_app_tenant_info):
        """When an exception occurs during display name query, should return applied_by"""
        mock_get_app_tenant_info.return_value = ("private", "tenant-2")
        mock_query_display_names.side_effect = Exception("Query error")

        result = ResourcePermissionHandler.convert_applied_by_to_display_name(
            bk_app_code="test-app",
            applied_by="admin",
            gateway_tenant_mode="global",
            gateway_tenant_id="tenant-1",
        )
        assert result == "admin"
        mock_get_app_tenant_info.assert_called_once_with("test-app")
        mock_query_display_names.assert_called_once_with("tenant-2", "admin")
