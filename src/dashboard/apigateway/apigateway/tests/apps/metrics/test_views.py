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
from django_dynamic_fixture import G

from apigateway.apps.metrics.views import QueryRangeAPIView
from apigateway.components.prometheus import QueryRangeResult
from apigateway.core.models import Stage
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, get_response_json


class TestQueryRangeAPIView:
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        self.factory = APIRequestFactory()
        self.gateway = create_gateway()
        self.stage = G(Stage, api=self.gateway, name="prod")

    def test_get(self, mocker, settings):
        settings.PROMETHEUS_METRIC_NAME_PREFIX = "apigateway_"

        data = [
            {
                "params": {
                    "stage_id": self.stage.id,
                    "resource_id": "",
                    "dimension": "all",
                    "metrics": "requests",
                    "time_range": 3600,
                },
                "mock_metrics": "apigateway.apps.metrics.helpers.RequestsMetrics",
                "mock_query_expression": (
                    'sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource=~".*"}[1m]))'
                ),
            },
            {
                "params": {
                    "stage_id": self.stage.id,
                    "resource_id": "",
                    "dimension": "all",
                    "metrics": "failed_requests",
                    "time_range": 3600,
                },
                "mock_metrics": "apigateway.apps.metrics.helpers.FailedRequestsMetrics",
                "mock_query_expression": (
                    'sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource=~".*", proxy_error="1"}[1m]))'
                ),
            },
            {
                "params": {
                    "stage_id": self.stage.id,
                    "resource_id": "",
                    "dimension": "all",
                    "metrics": "response_time_95th",
                    "time_range": 3600,
                },
                "mock_metrics": "apigateway.apps.metrics.helpers.ResponseTime95thMetrics",
                "mock_query_expression": (
                    "histogram_quantile(0.95, sum(rate(apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'job="apigateway", api="2", stage="prod", resource=~".*"}[1m])) by (le, api))'
                ),
            },
            {
                "params": {
                    "stage_id": self.stage.id,
                    "resource_id": "",
                    "dimension": "app",
                    "metrics": "requests",
                    "time_range": 3600,
                },
                "mock_metrics": "apigateway.apps.metrics.helpers.AppRequestsMetrics",
                "mock_query_expression": (
                    'topk(10, sum(increase(apigateway_apigateway_app_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource=~".*"}[1m])) by (api, app_code))'
                ),
            },
        ]

        for test in data:
            query_range = mocker.patch("apigateway.apps.metrics.views.prometheus_component.query_range")
            get_query_expression = mocker.patch(f'{test["mock_metrics"]}.get_query_expression')
            query_range.return_value = QueryRangeResult(
                **{
                    "resultType": "matrix",
                    "result": [
                        {
                            "metric": {
                                "api": "2",
                                "app_code": "test",
                            },
                            "values": [
                                [1582880683, "22698.666666666664"],
                            ],
                        }
                    ],
                }
            )
            get_query_expression.return_value = test["mock_query_expression"]

            request = self.factory.get(f"/apis/{self.gateway.id}/metrics/query_range/", data=test["params"])

            view = QueryRangeAPIView.as_view()
            response = view(request, gateway_id=self.gateway.id)
            result = get_response_json(response)

            assert response.status_code == 200, json.dumps(result)
            assert result["result"] is True
