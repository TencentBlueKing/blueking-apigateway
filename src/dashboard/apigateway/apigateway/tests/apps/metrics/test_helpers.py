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
from apigateway.apps.metrics import helpers


class TestDimensionMetricsManager:
    def test_create_dimension_metrics(self):
        data = [
            {
                "dimension": "all",
                "metrics": "requests",
                "expected": helpers.RequestsMetrics,
            },
            {
                "dimension": "all",
                "metrics": "failed_requests",
                "expected": helpers.FailedRequestsMetrics,
            },
            {
                "dimension": "all",
                "metrics": "response_time_95th",
                "expected": helpers.ResponseTime95thMetrics,
            },
            {
                "dimension": "all",
                "metrics": "response_time_50th",
                "expected": helpers.ResponseTime50thMetrics,
            },
            {
                "dimension": "resource",
                "metrics": "requests",
                "expected": helpers.ResourceRequestsMetrics,
            },
            {
                "dimension": "app",
                "metrics": "requests",
                "expected": helpers.AppRequestsMetrics,
            },
            {
                "dimension": "resource_non200_status",
                "metrics": "requests",
                "expected": helpers.ResourceNon200StatusRequestsMetrics,
            },
        ]
        for test in data:
            result = helpers.DimensionMetricsManager.create_dimension_metrics(
                test["dimension"],
                test["metrics"],
            )
            assert isinstance(result, test["expected"])


class TestRequestsMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource="1"}[1m]))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod"}[1m]))'
                ),
            },
        ]
        for test in data:
            metrics = helpers.RequestsMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"]


class TestFailedRequestsMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource="1", proxy_error="1"}[1m]))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", proxy_error="1"}[1m]))'
                ),
            },
        ]
        for test in data:
            metrics = helpers.FailedRequestsMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result


class TestResponseTime95thMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.95, sum(rate(apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'job="apigateway", api="2", stage="prod", resource="1"}[1m])) by (le, api))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.95, sum(rate(apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'job="apigateway", api="2", stage="prod"}[1m])) '
                    "by (le, api))"
                ),
            },
        ]
        for test in data:
            metrics = helpers.ResponseTime95thMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result


class TestResponseTime50thMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.5, sum(rate(apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'job="apigateway", api="2", stage="prod", resource="1"}[1m])) by (le, api))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.5, sum(rate(apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'job="apigateway", api="2", stage="prod"}[1m])) '
                    "by (le, api))"
                ),
            },
        ]
        for test in data:
            metrics = helpers.ResponseTime50thMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result


class TestResourceRequestsMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource="1"}[1m])) by (api, resource, path))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod"}[1m])) by (api, resource, path))'
                ),
            },
        ]
        for test in data:
            metrics = helpers.ResourceRequestsMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result


class TestResourceFailedRequestsMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource="1", proxy_error="1"}[1m])) by (api, resource, path))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", proxy_error="1"}[1m])) by (api, resource, path))'
                ),
            },
        ]
        for test in data:
            metrics = helpers.ResourceFailedRequestsMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result


class TestAppRequestsMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_app_requests_total{job="apigateway", api="2", '
                    'stage="prod", resource="1"}[1m])) by (api, app_code))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_app_requests_total{job="apigateway", api="2", '
                    'stage="prod"}[1m])) by (api, app_code))'
                ),
            },
        ]
        for test in data:
            metrics = helpers.AppRequestsMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result


class TestResourceNon200StatusRequestsMetrics:
    def test_get_query_expression(self, mocker):
        mocker.patch("apigateway.apps.metrics.helpers.BaseDimensionMetrics.default_labels", return_value=[])
        mocker.patch(
            "apigateway.apps.metrics.helpers.BasePrometheusMetrics.metric_name_prefix",
            new_callable=mocker.PropertyMock(return_value="apigateway_"),
        )

        data = [
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", status!="200", resource="1"}[1m])) by (api, resource, path, status))'
                ),
            },
            {
                "params": {
                    "gateway_id": 2,
                    "stage_name": "prod",
                    "resource_id": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(apigateway_apigateway_api_requests_total{job="apigateway", api="2", '
                    'stage="prod", status!="200"}[1m])) by (api, resource, path, status))'
                ),
            },
        ]
        for test in data:
            metrics = helpers.ResourceNon200StatusRequestsMetrics()
            result = metrics.get_query_expression(**test["params"])
            assert result == test["expected"], result
