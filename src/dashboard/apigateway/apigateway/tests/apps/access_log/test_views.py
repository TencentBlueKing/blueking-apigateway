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
import pytest
from django.conf import settings
from django_dynamic_fixture import G

from apigateway.apps.access_log.constants import ES_LOG_FIELDS
from apigateway.apps.access_log.views import LogTimeChartAPIView, LogViewSet, SearchLogsAPIView
from apigateway.common.signature import SignatureGenerator
from apigateway.core.models import Gateway, Stage
from apigateway.tests.utils.testing import get_response_json

pytestmark = pytest.mark.django_db


class TestLogTimeChartAPIView:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, settings, request_factory, fake_gateway):
        self.factory = request_factory
        self.api = fake_gateway
        self.stage = G(Stage, api=self.api)

        settings.ACCESS_LOG_CONFIG = {
            "es_client_type": "bk_log",
            "es_index": "test_index",
            "es_time_field_name": "dtEventTimeStamp",
        }

    @pytest.mark.parametrize(
        "mocked_time_chart",
        [
            {
                "series": [7, 7],
                "timeline": [1579054140, 1579054200],
            },
        ],
    )
    def test_get(self, mocker, mocked_time_chart):
        mocker.patch(
            "apigateway.apps.access_log.helpers.BKLogLogSearch.get_time_chart",
            return_value=mocked_time_chart,
        )

        params = {
            "stage_id": self.stage.id,
            "time_range": 300,
            "query": "api_id: 2",
        }

        request = self.factory.get(f"/apis/{self.api.id}/logs/timechart/", data=params)

        view = LogTimeChartAPIView.as_view()
        response = view(request, gateway_id=self.api.id)
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["result"]
        assert result["code"] == 0
        assert result["data"] == {
            "series": [7, 7],
            "timeline": [1579054140, 1579054200],
        }


class TestSearchLogsView:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, settings, request_factory, fake_gateway):
        self.factory = request_factory
        self.api = fake_gateway
        self.stage = G(Stage, api=self.api)

        settings.ACCESS_LOG_CONFIG = {
            "es_client_type": "bk_log",
            "es_index": "test_index",
            "es_time_field_name": "dtEventTimeStamp",
        }

    def test_get(self, mocker):
        mocker.patch(
            "apigateway.apps.access_log.helpers.BKLogLogSearch.search_logs",
            return_value=(3, [{"a": 1}, {"a": 2}, {"a": 3}]),
        )

        params = {
            "api_id": self.api.id,
            "stage_id": self.stage.id,
            "time_range": 300,
            "offset": 0,
            "limit": 3,
            "query": "api_id: 2",
        }

        request = self.factory.get(f"/apis/{self.api.id}/logs/", data=params)

        view = SearchLogsAPIView.as_view()
        response = view(request, gateway_id=self.api.id)
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["result"]
        assert result["code"] == 0
        assert result["data"]["count"] == 3
        assert len(result["data"]["results"]) == 3
        assert not result["data"]["has_next"]
        assert not result["data"]["has_previous"]
        assert result["data"]["fields"] == ES_LOG_FIELDS


class TestLogViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, settings, request_factory, fake_gateway):
        self.factory = request_factory
        self.api = fake_gateway

        settings.ACCESS_LOG_CONFIG = {
            "es_client_type": "bk_log",
            "es_index": "test_index",
            "es_time_field_name": "dtEventTimeStamp",
        }

    def test_link(self, mocker):
        mocker.patch(
            "apigateway.apps.access_log.views.time.time",
            return_value=1581324959,
        )
        mocker.patch(
            "apigateway.apps.access_log.views.random.randint",
            return_value=12345,
        )

        params = {
            "request_id": "2230d0e25b274cb98b57ca5d0946d0f7",
        }

        request = self.factory.post(f'/apis/{self.api.id}/logs/{params["request_id"]}/link/')

        view = LogViewSet.as_view({"post": "link"})
        response = view(request, gateway_id=self.api.id, request_id=params["request_id"])
        result = get_response_json(response)

        assert response.status_code == 200
        assert result["result"]
        assert result["code"] == 0

    def test_retrieve(self, mocker):
        mocker.patch(
            "apigateway.apps.access_log.helpers.BKLogLogSearch.search_logs",
            return_value=(1, [{"a": 1}]),
        )

        gateway = G(Gateway)

        data = [
            {
                "request_id": "2230d0e25b274cb98b57ca5d0946d0f7",
                "params": {
                    "bk_nonce": 12345,
                    "bk_timestamp": 1881403843,
                    "shared_by": "admin",
                },
                "expected": "",
            }
        ]
        for test in data:
            path = f'/apis/{gateway.id}/logs/{test["request_id"]}/'
            generator = SignatureGenerator(settings.LOG_LINK_SECRET)
            test["params"]["bk_signature"] = generator.generate_signature("GET", path, test["params"])

            request = self.factory.get(path, data=test["params"])

            view = LogViewSet.as_view({"get": "retrieve"}, api_permission_exempt=True)
            response = view(request, gateway_id=gateway.id, request_id=test["request_id"])
            result = get_response_json(response)

            assert response.status_code == 200
            assert result["result"]
            assert result["code"] == 0
            assert result["data"]["count"] == 1
