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

from apigateway.core.models import Stage, StageItemConfig
from apigateway.tests.utils.testing import get_response_json


class TestStageItemConfigViewSet:
    def test_retrieve(self, request_to_view, request_factory, fake_stage_item_config):
        fake_stage_item_config.config = {"nodes": [{"host": "1.0.0.1", "weight": 90}]}
        fake_stage_item_config.save()

        request = request_factory.get("")
        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item.configs.detail",
            path_params={
                "gateway_id": fake_stage_item_config.api.id,
                "stage_id": fake_stage_item_config.stage.id,
                "stage_item_id": fake_stage_item_config.stage_item.id,
            },
        )
        result = get_response_json(response)
        assert result["code"] == 0
        assert result["data"]["config"] == {
            "nodes": [
                {
                    "host": "1.0.0.1",
                    "weight": 90,
                }
            ]
        }

    def test_create(self, request_to_view, request_factory, fake_stage_item):
        request = request_factory.post("", data={"config": {"nodes": [{"host": "1.0.0.1:8000", "weight": 100}]}})
        request.gateway = fake_stage_item.api
        stage = G(Stage, api=fake_stage_item.api)
        response = request_to_view(
            request=request,
            view_name="apigateway.apps.stage_item.configs.detail",
            path_params={
                "gateway_id": fake_stage_item.api.id,
                "stage_id": stage.id,
                "stage_item_id": fake_stage_item.id,
            },
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert StageItemConfig.objects.filter(api=fake_stage_item.api).count() == 1

    def test_update(self, request_to_view, request_factory, fake_stage_item_config):
        request = request_factory.post("", data={"config": {"nodes": [{"host": "1.0.0.1:8000", "weight": 100}]}})
        request.gateway = fake_stage_item_config.api
        response = request_to_view(
            request=request,
            view_name="apigateway.apps.stage_item.configs.detail",
            path_params={
                "gateway_id": fake_stage_item_config.api.id,
                "stage_id": fake_stage_item_config.stage.id,
                "stage_item_id": fake_stage_item_config.stage_item.id,
            },
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert StageItemConfig.objects.filter(api=fake_stage_item_config.api).count() == 1

    def test_destroy(self, request_to_view, request_factory, fake_stage_item_config):
        request = request_factory.delete("")
        request.gateway = fake_stage_item_config.api

        response = request_to_view(
            request,
            view_name="apigateway.apps.stage_item.configs.detail",
            path_params={
                "gateway_id": fake_stage_item_config.api.id,
                "stage_id": fake_stage_item_config.stage.id,
                "stage_item_id": fake_stage_item_config.stage_item.id,
            },
        )

        result = get_response_json(response)
        assert result["code"] == 0
        assert not StageItemConfig.objects.filter(api=fake_stage_item_config.api).exists()
