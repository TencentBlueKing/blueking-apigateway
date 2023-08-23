# -*- coding: utf-8 -*-
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
import json

import pytest
from ddf import G

from apigateway.apps.micro_gateway.views import MicroGatewayViewSet
from apigateway.common.factories import SchemaFactory
from apigateway.core.models import MicroGateway
from apigateway.tests.utils.testing import create_gateway, get_response_json

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture()
def mock_micro_gateway_config():
    return {
        "bcs": {
            "project_name": "demo",
            "project_id": "eaccf209c7f14e8bb90874566be63c9f",
            "cluster_id": "demo-cluster",
            "namespace": "demo-namespace",
            "chart_name": "bk-micro-gateway",
            "chart_version": "1.0.0",
            "release_name": "bkapigw-demo",
        },
        "http": {
            "http_url": "http://demo-bkapi.example.com",
        },
        "jwt_auth": {
            "secret_key": "eaccf209c7f14e8bb90874566be63c9f",
        },
    }


class TestMicroGatewayViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, request_factory):
        self.factory = request_factory
        self.gateway = create_gateway()

    @pytest.mark.parametrize(
        "data, need_deploy, will_error",
        [
            (
                {
                    "create_way": "need_deploy",
                    "name": "color-green",
                    "description": "test",
                },
                True,
                False,
            ),
            (
                {
                    "create_way": "relate_deployed",
                    "name": "color-green",
                    "description": "test",
                },
                False,
                False,
            ),
            (
                {
                    "create_way": "need_deploy",
                    "name": "invalid_name#",
                    "description": "test",
                },
                False,
                True,
            ),
        ],
    )
    def test_create(
        self,
        mocker,
        request_view,
        fake_admin_user,
        fake_gateway,
        mock_micro_gateway_config,
        data,
        need_deploy,
        will_error,
    ):
        mock_deploy_micro_gateway = mocker.patch(
            "apigateway.apps.micro_gateway.handlers.deploy_micro_gateway.apply_async"
        )

        data["bcs_info"] = mock_micro_gateway_config["bcs"]
        data["http_info"] = mock_micro_gateway_config["http"]

        response = request_view(
            "POST",
            "apigateway.apps.micro_gateway",
            gateway=self.gateway,
            path_params={
                "gateway_id": self.gateway.id,
            },
            data=data,
            user=fake_admin_user,
        )

        result = get_response_json(response)

        if will_error:
            assert response.status_code != 200, result
        else:
            assert response.status_code == 200, result

        if need_deploy:
            mock_deploy_micro_gateway.assert_called_once_with(
                args=(result["data"]["id"], "access_token", fake_admin_user.username), ignore_result=True, kwargs={}
            )
        else:
            mock_deploy_micro_gateway.assert_not_called()

    def test_list(self, mock_micro_gateway_config):
        micro_gateway = G(
            MicroGateway,
            gateway=self.gateway,
            _config=json.dumps(mock_micro_gateway_config),
            schema=SchemaFactory().get_micro_gateway_schema(),
        )

        view = MicroGatewayViewSet.as_view({"get": "list"})
        request = self.factory.get("")
        response = view(request, gateway_id=self.gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert len(result["data"]["results"]) == 1

    def test_update(self, request_view, fake_gateway, fake_admin_user, mock_micro_gateway_config, faker):
        micro_gateway = G(
            MicroGateway,
            gateway=self.gateway,
            _config=json.dumps(mock_micro_gateway_config),
            schema=SchemaFactory().get_micro_gateway_schema(),
        )

        expected_name = "micro-2"
        # request = self.factory.put(
        #     f"",
        #     data={
        #         "need_deploy": False,
        #         "name": expected_name,
        #         "description": "test",
        #         "http_info": {
        #             "http_url": "http://demo-bkapi.example.com",
        #         },
        #     },
        # )

        # view = MicroGatewayViewSet.as_view({"put": "update"})
        # response = view(request, gateway_id=self.gateway.id, id=micro_gateway.id)

        response = request_view(
            "PUT",
            "apigateway.apps.micro_gateway.detail",
            gateway=self.gateway,
            path_params={
                "gateway_id": self.gateway.id,
                "id": micro_gateway.id,
            },
            data={
                "need_deploy": False,
                "name": expected_name,
                "description": "test",
                "http_info": {
                    "http_url": "http://demo-bkapi.example.com",
                },
            },
            user=fake_admin_user,
        )

        result = get_response_json(response)
        assert result["code"] == 0, result

        micro_gateway = MicroGateway.objects.get(id=micro_gateway.id)
        assert micro_gateway.name == expected_name

    def test_retrieve(self, mock_micro_gateway_config):
        micro_gateway = G(
            MicroGateway,
            gateway=self.gateway,
            _config=json.dumps(mock_micro_gateway_config),
            schema=SchemaFactory().get_micro_gateway_schema(),
        )

        view = MicroGatewayViewSet.as_view({"get": "retrieve"})
        request = self.factory.get("")
        response = view(request, gateway_id=self.gateway.id, id=micro_gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0

    def test_destroy(self):
        micro_gateway = G(MicroGateway, gateway=self.gateway)
        micro_gateway_id = micro_gateway.id

        request = self.factory.delete("")
        view = MicroGatewayViewSet.as_view({"delete": "destroy"})
        response = view(request, gateway_id=self.gateway.id, id=micro_gateway.id)

        result = get_response_json(response)
        assert result["code"] == 0
        assert not MicroGateway.objects.filter(id=micro_gateway_id).exists()
