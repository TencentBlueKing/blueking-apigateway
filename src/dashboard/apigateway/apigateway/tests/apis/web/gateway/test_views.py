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
from apigateway.apps.gateway.models import GatewayAppBinding
from apigateway.biz.gateway import GatewayHandler
from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import JWT, Gateway, Stage


class TestGatewayListCreateApi:
    def test_list(self, request_view, fake_gateway):
        resp = request_view(
            method="GET",
            view_name="gateways.list_create",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) >= 1

    def test_create(self, request_view, faker, unique_gateway_name):
        data = {
            "name": unique_gateway_name,
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": False,
            "bk_app_codes": ["app1"],
        }

        resp = request_view(
            method="POST",
            view_name="gateways.list_create",
            data=data,
        )
        result = resp.json()

        assert resp.status_code == 201

        gateway = Gateway.objects.get(name=unique_gateway_name)
        assert result["data"]["id"] == gateway.id
        assert Stage.objects.filter(gateway=gateway).exists()
        assert JWT.objects.filter(gateway=gateway).count() == 1
        assert GatewayAppBinding.objects.filter(gateway=gateway).count() == 1

        auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
        assert auth_config["allow_auth_from_params"] is False
        assert auth_config["allow_delete_sensitive_params"] is False


class TestGatewayRetrieveUpdateDestroyApi:
    def test_retrieve(self, request_view, fake_gateway):
        GatewayJWTHandler.create_jwt(fake_gateway)
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        resp = request_view(
            method="GET",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_gateway.id

    def test_update(self, request_view, faker, fake_gateway):
        data = {
            "description": faker.pystr(),
            "maintainers": ["admin"],
            "is_public": faker.random_element([True, False]),
            "bk_app_codes": ["app1"],
            "related_app_codes": ["app2"],
        }
        resp = request_view(
            method="PUT",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        gateway = Gateway.objects.get(id=fake_gateway.id)

        assert resp.status_code == 204
        assert gateway.description == data["description"]
        assert gateway.is_public is data["is_public"]
        assert GatewayAppBinding.objects.filter(gateway=gateway).count() == 1

        auth_config = GatewayHandler.get_gateway_auth_config(gateway.id)
        assert "allow_auth_from_params" not in auth_config
        assert "allow_delete_sensitive_params" not in auth_config

    def test_destroy(self, request_view, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="DELETE",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )

        assert resp.status_code == 204
        assert fake_gateway.id is not None
        assert not Gateway.objects.filter(id=fake_gateway.id).exists()

    def test_destroy__failed(self, request_view, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        resp = request_view(
            method="DELETE",
            view_name="gateways.retrieve_update_destroy",
            path_params={"gateway_id": fake_gateway.id},
        )

        assert resp.status_code == 400


class TestGatewayUpdateStatusApi:
    def test_update(self, request_view, faker, fake_gateway):
        data = {
            "status": faker.random_element(GatewayStatusEnum.get_values()),
        }
        resp = request_view(
            method="PUT",
            view_name="gateways.update_status",
            path_params={"gateway_id": fake_gateway.id},
            data=data,
        )
        gateway = Gateway.objects.get(id=fake_gateway.id)

        assert resp.status_code == 204
        assert gateway.status == data["status"]
