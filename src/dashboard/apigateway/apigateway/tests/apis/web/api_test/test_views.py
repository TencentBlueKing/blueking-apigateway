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
import responses
from ddf import G

from apigateway.core.models import ResourceDebugHistory
from apigateway.core.utils import get_resource_url


class TestAPITestAPIView:
    @responses.activate
    def test_post(self, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"

        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        responses.add(
            fake_resource1.method,
            url,
            body="a" * 3000,
            adding_headers={
                "x-token": "test",
            },
            content_type="text/plain",
        )

        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": fake_resource1.method,
                "headers": {},
                "path_params": {},
                "query_params": {},
                "body": "",
                "use_test_app": True,
            },
        )

        result = response.json()
        assert response.status_code == 200
        assert result["data"]["headers"] == {
            "Content-Type": "text/plain",
            "x-token": "test",
        }


class TestAPIDebugHistoryApi:
    def test_list(self, request_view, fake_resource, fake_gateway):
        G(ResourceDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway, request_url="url1")
        G(ResourceDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway, request_url="url2")
        G(ResourceDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway, request_url="url3")
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id},
            view_name="api_debug.histories.list",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 3

    def test_retrieve(self, request_view, fake_gateway, fake_resource):
        fake_history = G(
            ResourceDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway, request_url="url1"
        )
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id, "id": fake_history.id},
            view_name="api_debug.histories.retrieve-destroy",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_history.id

    def test_destroy(self, request_view, fake_gateway, fake_resource):
        fake_history = G(
            ResourceDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway, request_url="url1"
        )
        resp = request_view(
            method="DELETE",
            path_params={"gateway_id": fake_gateway.id, "id": fake_history.id},
            view_name="api_debug.histories.retrieve-destroy",
        )

        assert resp.status_code == 204
