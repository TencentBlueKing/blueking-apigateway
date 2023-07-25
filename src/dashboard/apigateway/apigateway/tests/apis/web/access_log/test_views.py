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

from apigateway.apis.web.access_log.constants import ES_LOG_FIELDS

pytestmark = pytest.mark.django_db


class TestLogTimeChartAPIView:
    @pytest.mark.parametrize(
        "mocked_time_chart",
        [
            {
                "series": [7, 7],
                "timeline": [1579054140, 1579054200],
            },
        ],
    )
    def test_get(self, request_view, mocker, fake_stage, mocked_time_chart):
        mocker.patch(
            "apigateway.apis.web.access_log.views.LogSearchClient.get_time_chart",
            return_value=mocked_time_chart,
        )

        fake_gateway = fake_stage.api

        response = request_view(
            "GET",
            "access_log.logs.time_chart",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "time_range": 300,
                "query": "api_id: 2",
            },
        )
        result = response.json()
        assert result["code"] == 0
        assert result["data"] == {
            "series": [7, 7],
            "timeline": [1579054140, 1579054200],
        }


class TestSearchLogsView:
    def test_get(self, mocker, request_view, fake_stage):
        mocker.patch(
            "apigateway.apis.web.access_log.views.LogSearchClient.search_logs",
            return_value=(3, [{"a": 1}, {"a": 2}, {"a": 3}]),
        )

        fake_gateway = fake_stage.api

        response = request_view(
            "GET",
            "access_log.logs",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "time_range": 300,
                "offset": 0,
                "limit": 3,
                "query": "api_id: 2",
            },
        )
        result = response.json()

        assert result["code"] == 0
        assert result["data"]["count"] == 3
        assert len(result["data"]["results"]) == 3
        assert not result["data"]["has_next"]
        assert not result["data"]["has_previous"]
        assert result["data"]["fields"] == ES_LOG_FIELDS


class TestLogDetailAPIView:
    def test_get(self, mocker, request_view, fake_gateway):
        mocker.patch(
            "apigateway.apis.web.access_log.views.LogSearchClient.search_logs",
            return_value=(1, [{"a": 1}]),
        )
        mocker.patch("apigateway.apis.web.access_log.views.SignatureValidator.is_valid")

        response = request_view(
            "GET",
            "access_log.logs.detail",
            path_params={"gateway_id": fake_gateway.id, "request_id": "2230d0e25b274cb98b57ca5d0946d0f7"},
            gateway=fake_gateway,
            data={
                "bk_nonce": 12345,
                "bk_timestamp": 1881403843,
                "shared_by": "admin",
            },
        )
        result = response.json()

        assert result["code"] == 0
        assert result["data"]["count"] == 1
        assert result["data"]["fields"] == ES_LOG_FIELDS


class TestLogLinkAPIView:
    def test_link(self, request_view, fake_gateway):
        response = request_view(
            "POST",
            "access_log.logs.link",
            path_params={
                "gateway_id": fake_gateway.id,
                "request_id": "2230d0e25b274cb98b57ca5d0946d0f7",
            },
            gateway=fake_gateway,
        )
        result = response.json()

        assert result["code"] == 0
        assert result["data"]["link"]
