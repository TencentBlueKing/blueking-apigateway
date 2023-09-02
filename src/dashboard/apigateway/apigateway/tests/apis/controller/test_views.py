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
from functools import partial

import pytest
from ddf import G

from apigateway.apps.permission.models import AppAPIPermission, AppResourcePermission


class TestMicroGatewayPermissionViewSet:
    @pytest.fixture(autouse=True)
    def setup(self, fake_gateway, fake_resource1, fake_resource2, patch_redis):
        self.app1 = "app-a"
        self.app2 = "app-b"

        G(AppAPIPermission, bk_app_code=self.app1, gateway=fake_gateway)
        G(AppResourcePermission, bk_app_code=self.app1, gateway=fake_gateway, resource_id=fake_resource1.id)

        G(AppAPIPermission, bk_app_code=self.app2, gateway=fake_gateway)
        G(AppResourcePermission, bk_app_code=self.app2, gateway=fake_gateway, resource_id=fake_resource1.id)
        G(AppResourcePermission, bk_app_code=self.app2, gateway=fake_gateway, resource_id=fake_resource2.id)

    def is_app_has_api_permission(self, result, gateway, app_code):
        api_permissions = result["data"]["api_permissions"]
        assert result["data"]["gateway_name"] == gateway.name
        for permission in api_permissions:
            if permission["bk_app_code"] == app_code:
                return True

        return False

    def is_app_has_resource_permission(self, result, app_code, resource_name):
        resource_permissions = result["data"]["resource_permissions"]
        for permission in resource_permissions:
            if permission["bk_app_code"] == app_code and permission["resource_name"] == resource_name:
                return True

        return False

    def test_list_by_gateway(
        self,
        request_view,
        fake_shared_gateway,
        fake_release,
        fake_resource1,
        fake_resource2,
        skip_view_permissions_check,
        fake_gateway,
        fake_stage,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_permissions",
            {
                "instance_id": fake_shared_gateway.id,
            },
            data={
                "gateway_name": fake_gateway.name,
                "stage_name": fake_stage.name,
            },
        )

        result = response.json()
        assert self.is_app_has_api_permission(result, fake_gateway, self.app1)
        assert self.is_app_has_resource_permission(result, self.app1, fake_resource1.name)
        assert not self.is_app_has_resource_permission(result, self.app1, fake_resource2.name)

        assert self.is_app_has_api_permission(result, fake_gateway, self.app2)
        assert self.is_app_has_resource_permission(result, self.app2, fake_resource1.name)
        assert self.is_app_has_resource_permission(result, self.app2, fake_resource2.name)

    def test_list_by_gateway_cache(
        self,
        mocker,
        default_redis,
        request_view,
        fake_shared_gateway,
        fake_release,
        fake_resource1,
        fake_resource2,
        skip_view_permissions_check,
        fake_gateway,
        fake_stage,
    ):
        request_fn = partial(
            request_view,
            "GET",
            "apigateway.controller.micro_gateway_permissions",
            {
                "instance_id": fake_shared_gateway.id,
            },
            data={
                "gateway_name": fake_gateway.name,
                "stage_name": fake_stage.name,
            },
        )

        mocker.patch("apigateway.apis.controller.views.get_default_redis_client", return_value=default_redis)

        first_requested = request_fn().json()

        patched_get_permissions_from_db = mocker.patch(
            "apigateway.apis.controller.views.MicroGatewayPermissionViewSet._get_permissions_from_db"
        )

        second_requested = request_fn().json()

        patched_get_permissions_from_db.assert_not_called()
        assert first_requested == second_requested

    def test_list_by_app(
        self,
        request_view,
        fake_edge_gateway,
        fake_release,
        fake_resource1,
        fake_resource2,
        skip_view_permissions_check,
        fake_gateway,
        fake_stage,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_permissions",
            {
                "instance_id": fake_edge_gateway.id,
            },
            data={
                "gateway_name": fake_gateway.name,
                "stage_name": fake_stage.name,
                "target_app_code": self.app1,
            },
        )

        result = response.json()
        assert self.is_app_has_api_permission(result, fake_gateway, self.app1)
        assert self.is_app_has_resource_permission(result, self.app1, fake_resource1.name)

        assert not self.is_app_has_api_permission(result, fake_gateway, self.app2)
        assert not self.is_app_has_resource_permission(result, self.app2, fake_resource1.name)
        assert not self.is_app_has_resource_permission(result, self.app2, fake_resource2.name)

    def test_list_by_app_from_cache(
        self,
        mocker,
        request_view,
        default_redis,
        fake_edge_gateway,
        fake_release,
        fake_resource1,
        fake_resource2,
        skip_view_permissions_check,
        fake_gateway,
        fake_stage,
    ):
        request_fn = partial(
            request_view,
            "GET",
            "apigateway.controller.micro_gateway_permissions",
            {
                "instance_id": fake_edge_gateway.id,
            },
            data={
                "gateway_name": fake_gateway.name,
                "stage_name": fake_stage.name,
                "target_app_code": self.app1,
            },
        )

        mocker.patch("apigateway.apis.controller.views.get_default_redis_client", return_value=default_redis)

        first_requested = request_fn().json()

        patched_get_permissions_from_db = mocker.patch(
            "apigateway.apis.controller.views.MicroGatewayPermissionViewSet._get_permissions_from_db"
        )

        second_requested = request_fn().json()

        patched_get_permissions_from_db.assert_not_called()
        assert first_requested == second_requested

    def test_not_released_permissions(
        self,
        request_view,
        fake_edge_gateway,
        fake_gateway,
        fake_stage,
        skip_view_permissions_check,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_permissions",
            {
                "instance_id": fake_edge_gateway.id,
            },
            data={
                "gateway_name": fake_gateway.name,
                "stage_name": fake_stage.name,
            },
        )

        assert response.status_code == 200

        result = response.json()
        assert self.is_app_has_api_permission(result, fake_gateway, self.app1)


class TestMicroGatewayNewestPermissionViewSet:
    @pytest.fixture(autouse=True)
    def setup(self, default_redis, request_view, skip_view_permissions_check, fake_resource):
        self.default_redis = default_redis
        self.request_view = request_view
        self.resource = fake_resource.name
        self.app = "app"

    def request_newest_gateway_permissions(self, micro_gateway, gateway_name):
        return self.request_view(
            "GET",
            "apigateway.controller.micro_gateway_permissions.gateway-newest",
            {"instance_id": micro_gateway.id},
            data={
                "gateway_name": gateway_name,
                "target_app_code": self.app,
            },
        )

    def request_newest_resource_permissions(self, micro_gateway, gateway_name):
        return self.request_view(
            "GET",
            "apigateway.controller.micro_gateway_permissions.resource-newest",
            {"instance_id": micro_gateway.id},
            data={
                "gateway_name": gateway_name,
                "resource_name": self.resource,
                "target_app_code": self.app,
            },
        )

    def test_list_invalid_gateway_permissions(self, faker, fake_micro_gateway):
        response = self.request_newest_gateway_permissions(fake_micro_gateway, faker.word())

        assert response.status_code == 403

    def test_list_invalid_resource_permissions(self, faker, fake_micro_gateway):
        response = self.request_newest_resource_permissions(fake_micro_gateway, faker.word())

        assert response.status_code == 403

    def test_list_empty_gateway_permissions(self, fake_micro_gateway, fake_gateway):
        response = self.request_newest_gateway_permissions(fake_micro_gateway, fake_gateway.name)

        result = response.json()
        data = result["data"]

        assert data["gateway_name"] == fake_gateway.name
        assert data["api_permissions"] == []

    def test_list_empty_resource_permissions(self, fake_micro_gateway, fake_gateway):
        response = self.request_newest_resource_permissions(fake_micro_gateway, fake_gateway.name)

        result = response.json()
        data = result["data"]

        assert data["gateway_name"] == fake_gateway.name
        assert data["resource_permissions"] == []

    def test_list_gateway_permissions(self, fake_micro_gateway, fake_gateway, default_redis):
        G(AppAPIPermission, gateway=fake_gateway, bk_app_code=self.app)

        response = self.request_newest_gateway_permissions(fake_micro_gateway, fake_gateway.name)

        result = response.json()
        data = result["data"]
        permission = data["api_permissions"][0]
        assert permission["bk_app_code"] == self.app

    def test_list_resource_permissions(self, fake_micro_gateway, fake_gateway, fake_resource, default_redis):
        G(AppResourcePermission, gateway=fake_gateway, bk_app_code=self.app, resource_id=fake_resource.id)

        response = self.request_newest_resource_permissions(fake_micro_gateway, fake_gateway.name)

        result = response.json()
        data = result["data"]
        permission = data["resource_permissions"][0]
        assert permission["bk_app_code"] == self.app


class TestMicroGatewayInfoViewSet:
    def test_shared_gateway(
        self,
        request_view,
        fake_shared_gateway,
        skip_view_permissions_check,
        fake_gateway,
        fake_stage,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_info",
            {
                "instance_id": fake_shared_gateway.id,
            },
        )
        result = response.json()
        info = result["data"]

        assert info["name"] == fake_shared_gateway.name

        found = False
        for info in info["related_infos"]:
            if info["gateway_name"] == fake_gateway.name and info["stage_name"] == fake_stage.name:
                found = True
                break

        assert found

    def test_edge_gateway(
        self,
        request_view,
        fake_edge_gateway,
        fake_stage,
        skip_view_permissions_check,
        fake_gateway,
    ):
        response = request_view(
            "GET",
            "apigateway.controller.micro_gateway_info",
            {
                "instance_id": fake_edge_gateway.id,
            },
        )
        result = response.json()
        info = result["data"]

        assert info["name"] == fake_edge_gateway.name

        found = False
        for info in info["related_infos"]:
            if info["gateway_name"] == fake_gateway.name and info["stage_name"] == fake_stage.name:
                found = True
                break

        assert found
        assert found
