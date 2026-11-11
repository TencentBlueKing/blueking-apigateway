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
import pytest
from rest_framework.permissions import IsAuthenticated

from apigateway.apis.web.docs.gateway.gateway.views import GatewayRetrieveApi
from apigateway.apis.web.docs.gateway.gateway_sdk.views import SDKListApi, SDKUsageExampleApi
from apigateway.apis.web.docs.gateway.permission.views import GatewayPermissionApplyCreateApi
from apigateway.apis.web.docs.gateway.permissions import GatewayDisplayablePermission
from apigateway.apis.web.docs.gateway.resource.doc.views import DocRetrieveApi
from apigateway.apis.web.docs.gateway.resource.views import ResourceListApi
from apigateway.apis.web.docs.gateway.stage.views import StageListApi
from apigateway.core.constants import GatewaySourceEnum


class TestDocsGatewayPermissionClasses:
    def test_permission_classes_contains_authenticated(self):
        view_classes = [
            GatewayRetrieveApi,
            GatewayPermissionApplyCreateApi,
            SDKListApi,
            SDKUsageExampleApi,
            DocRetrieveApi,
            ResourceListApi,
            StageListApi,
        ]

        for view_class in view_classes:
            assert IsAuthenticated in view_class.permission_classes
            assert GatewayDisplayablePermission in view_class.permission_classes


class TestDocsGatewayTenantIsolation:
    @pytest.mark.parametrize("source", ["", GatewaySourceEnum.API_DEBUG.value])
    @pytest.mark.parametrize(
        ("tenant_mode", "gateway_tenant_id", "user_tenant_id", "expected_status"),
        [
            ("single", "tenant-a", "tenant-a", 200),
            ("single", "tenant-b", "tenant-a", 404),
            ("single", "tenant-b", "system", 404),
            ("global", "", "tenant-a", 200),
            ("global", "", "system", 200),
        ],
    )
    def test_gateway_visibility(
        self,
        settings,
        request_view,
        fake_gateway,
        fake_admin_user,
        source,
        tenant_mode,
        gateway_tenant_id,
        user_tenant_id,
        expected_status,
    ):
        settings.ENABLE_MULTI_TENANT_MODE = True
        fake_gateway.tenant_mode = tenant_mode
        fake_gateway.tenant_id = gateway_tenant_id
        fake_gateway.save(update_fields=["tenant_mode", "tenant_id"])
        fake_admin_user.is_superuser = False
        fake_admin_user.tenant_id = user_tenant_id

        response = request_view(
            method="GET",
            view_name="docs.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
            user=fake_admin_user,
            data={"source": source},
        )

        assert response.status_code == expected_status
        if expected_status == 200:
            assert response.json()["data"]["id"] == fake_gateway.id

    @pytest.mark.parametrize("source", ["", GatewaySourceEnum.API_DEBUG.value])
    def test_gateway_access_after_tenant_switch(self, settings, request_view, fake_gateway, fake_admin_user, source):
        settings.ENABLE_MULTI_TENANT_MODE = True
        fake_gateway.tenant_id = "tenant-a"
        fake_gateway.save(update_fields=["tenant_id"])
        fake_admin_user.is_superuser = False

        for tenant_id, expected_status in [("tenant-a", 200), ("tenant-b", 404)]:
            fake_admin_user.tenant_id = tenant_id
            response = request_view(
                method="GET",
                view_name="docs.gateway.retrieve",
                path_params={"gateway_name": fake_gateway.name},
                user=fake_admin_user,
                data={"source": source},
            )

            assert response.status_code == expected_status

    @pytest.mark.parametrize("source", ["", GatewaySourceEnum.API_DEBUG.value])
    @pytest.mark.parametrize(
        ("method", "view_name", "extra_path_params"),
        [
            ("GET", "docs.gateway.stage.list", {}),
            ("GET", "docs.gateway.resource.list", {}),
            ("GET", "docs.gateway.resource.doc.retrieve", {"resource_name": "test-resource"}),
            ("GET", "docs.gateway.gateway_sdk.list", {}),
            ("GET", "docs.gateway.gateway_sdk.retrieve_usage_example", {}),
            ("POST", "docs.gateway.permission.apply", {}),
        ],
    )
    def test_subresource_rejects_other_tenant(
        self, settings, request_view, fake_gateway, fake_admin_user, source, method, view_name, extra_path_params
    ):
        settings.ENABLE_MULTI_TENANT_MODE = True
        fake_gateway.tenant_id = "tenant-b"
        fake_gateway.save(update_fields=["tenant_id"])
        fake_admin_user.is_superuser = False
        fake_admin_user.tenant_id = "tenant-a"

        response = request_view(
            method=method,
            view_name=view_name,
            path_params={"gateway_name": fake_gateway.name, **extra_path_params},
            user=fake_admin_user,
            # POST must also select the debug branch through the query string.
            QUERY_STRING=f"source={source}",
        )

        assert response.status_code == 404

    @pytest.mark.parametrize(
        ("source", "username", "expected_status"),
        [
            ("", "admin", 404),
            (GatewaySourceEnum.API_DEBUG.value, "admin", 200),
            (GatewaySourceEnum.API_DEBUG.value, "non-admin", 404),
        ],
    )
    def test_debug_requires_gateway_administrator(
        self, settings, request_view, fake_gateway, fake_admin_user, source, username, expected_status
    ):
        settings.ENABLE_MULTI_TENANT_MODE = True
        fake_gateway.tenant_id = "tenant-a"
        fake_gateway.is_public = False
        fake_gateway.status = 0
        fake_gateway.save(update_fields=["tenant_id", "is_public", "status"])
        fake_admin_user.username = username
        fake_admin_user.is_superuser = False
        fake_admin_user.tenant_id = "tenant-a"

        response = request_view(
            method="GET",
            view_name="docs.gateway.retrieve",
            path_params={"gateway_name": fake_gateway.name},
            user=fake_admin_user,
            data={"source": source},
        )

        assert response.status_code == expected_status
