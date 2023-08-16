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

from apigateway.core.models import BackendService, StageItem
from apigateway.tests.utils.testing import get_response_json


class TestStageItemViewSet:
    def test_list(self, request_to_view, request_factory, fake_stage_item):
        request = request_factory.get("")
        request.gateway = fake_stage_item.api

        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item",
            path_params={"gateway_id": fake_stage_item.api.id},
        )
        result = get_response_json(response)

        assert result["code"] == 0
        assert len(result["data"]) == 1

    def test_retrieve(self, request_to_view, request_factory, fake_stage_item_config):
        fake_stage_item = fake_stage_item_config.stage_item
        request = request_factory.get("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item.detail",
            path_params={"gateway_id": fake_stage_item.api.id, "id": fake_stage_item.id},
        )
        result = get_response_json(response)

        assert result["code"] == 0
        assert result["data"]["type"] == "node"
        assert result["data"]["stage_item_configs"] == [
            {
                "stage_id": fake_stage_item_config.stage.id,
                "stage_name": fake_stage_item_config.stage.name,
                "config": {"nodes": [{"host": "1.0.0.1", "weight": 100}]},
            }
        ]

    def test_create(self, request_to_view, request_factory, fake_gateway):
        request = request_factory.post("", data={"type": "node", "name": "item", "description": "desc"})
        request.gateway = fake_gateway

        response = request_to_view(
            request=request,
            view_name="apigateway.apps.stage_item",
            path_params={"gateway_id": fake_gateway.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0, result

        assert StageItem.objects.filter(api=fake_gateway).count() == 1

    def test_update(self, request_to_view, request_factory, fake_stage_item):
        request = request_factory.put("", data={"type": "node", "name": "another-item"})
        request.gateway = fake_stage_item.api

        response = request_to_view(
            request=request,
            view_name="apigateway.apps.stage_item.detail",
            path_params={"gateway_id": fake_stage_item.api.id, "id": fake_stage_item.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert StageItem.objects.get(id=fake_stage_item.id).name == "another-item"

    def test_destroy(self, request_to_view, request_factory, fake_stage_item):
        fake_gateway = fake_stage_item.api
        request = request_factory.delete("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item.detail",
            path_params={"gateway_id": fake_gateway.id, "id": fake_stage_item.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0

        assert not StageItem.objects.filter(api=fake_gateway).exists()

    def test_destroy_error(self, request_to_view, request_factory, fake_stage_item):
        G(BackendService, api=fake_stage_item.api, stage_item=fake_stage_item)

        request = request_factory.delete("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item.detail",
            path_params={"gateway_id": fake_stage_item.api.id, "id": fake_stage_item.id},
        )

        # result = get_response_json(response)
        assert response.status_code != 200

        assert StageItem.objects.filter(api=fake_stage_item.api).exists()


class TestStageItemForStageViewSet:
    def test_list(self, request_factory, request_to_view, fake_stage_item_config):
        fake_gateway = fake_stage_item_config.api
        fake_stage = fake_stage_item_config.stage
        G(StageItem, api=fake_gateway)

        request = request_factory.get("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item.for_stage",
            path_params={"gateway_id": fake_gateway.id, "stage_id": fake_stage.id},
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"][0]["status"] == "configured"
        assert result["data"][1]["status"] == "not_configured"
