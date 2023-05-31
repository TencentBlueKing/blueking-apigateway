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
from ddf import G

from apigateway.core.models import BackendService
from apigateway.tests.utils.testing import get_response_json


class TestBackendServiceViewSet:
    def test_create(
        self,
        mocker,
        request_to_view,
        request_factory,
        fake_gateway,
        fake_node_data,
    ):
        request = request_factory.post("", data=fake_node_data)
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="apigateway.apps.backend_service",
            path_params={"gateway_id": fake_gateway.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0, result

        assert BackendService.objects.filter(api=fake_gateway).count() == 1

    def test_update(self, request_to_view, request_factory, fake_gateway, fake_node_data):
        instance = G(BackendService, api=fake_gateway)

        request = request_factory.put("", data=fake_node_data)
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="apigateway.apps.backend_service.detail",
            path_params={"gateway_id": fake_gateway.id, "id": instance.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert BackendService.objects.get(id=instance.id).name == fake_node_data["name"]

    def test_list(self, request_to_view, request_factory, fake_gateway):
        G(BackendService, api=fake_gateway)

        request = request_factory.get("")
        request.gateway = fake_gateway

        response = request_to_view(
            request, view_name="apigateway.apps.backend_service", path_params={"gateway_id": fake_gateway.id}
        )
        result = get_response_json(response)

        assert result["code"] == 0
        assert len(result["data"]["results"]) == 1

    def test_retrieve(self, request_to_view, request_factory, fake_gateway, fake_node_data):
        instance = G(BackendService, api=fake_gateway, **fake_node_data)

        request = request_factory.get("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.backend_service.detail",
            path_params={"gateway_id": fake_gateway.id, "id": instance.id},
        )
        result = get_response_json(response)

        assert result["code"] == 0

    def test_destroy(self, request_to_view, request_factory, fake_gateway):
        instance = G(BackendService, api=fake_gateway)

        request = request_factory.delete("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.backend_service.detail",
            path_params={"gateway_id": fake_gateway.id, "id": instance.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert BackendService.objects.filter(api=fake_gateway).count() == 0
