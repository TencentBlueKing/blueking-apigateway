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
from apigateway.apps.metrics.constants import DimensionEnum, MetricsEnum
from apigateway.apps.metrics.prometheus import dimension


class TestRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo"}[1m]))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod"}[1m]))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.RequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"]


class TestFailedRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo", status=~"5.."}[1m]))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status=~"5.."}[1m]))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.FailedRequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResponseTime95thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.95, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", resource_name="get_foo"}[1m])) by (le, api_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.95, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, api_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime95thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResponseTime50thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.5, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", resource_name="get_foo"}[1m])) by (le, api_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.5, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, api_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime50thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResourceRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo"}[1m])) by (api_name, resource_name, matched_uri))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod"}[1m])) by (api_name, resource_name, matched_uri))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResourceRequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResourceFailedRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo", status=~"5.."}[1m])) by (api_name, resource_name, matched_uri))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status=~"5.."}[1m])) by (api_name, resource_name, matched_uri))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResourceFailedRequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestAppRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_app_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo"}[1m])) by (api_name, app_code))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_app_requests_total{api_name="foo", '
                    'stage_name="prod"}[1m])) by (api_name, app_code))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.AppRequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResourceNon200StatusRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch(
            "apigateway.apps.metrics.prometheus.dimension.BaseDimensionMetrics.default_labels", return_value=[]
        )

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo", status!="200"}[1m])) by (api_name, resource_name, matched_uri, status))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status!="200"}[1m])) by (api_name, resource_name, matched_uri, status))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResourceNon200StatusRequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestDimensionMetricsFactory:
    def test_create_dimension_metrics(self):
        data = [
            {
                "dimension": "all",
                "metrics": "requests",
                "expected": dimension.RequestsMetrics,
            },
            {
                "dimension": "all",
                "metrics": "failed_requests",
                "expected": dimension.FailedRequestsMetrics,
            },
            {
                "dimension": "all",
                "metrics": "response_time_95th",
                "expected": dimension.ResponseTime95thMetrics,
            },
            {
                "dimension": "all",
                "metrics": "response_time_50th",
                "expected": dimension.ResponseTime50thMetrics,
            },
            {
                "dimension": "resource",
                "metrics": "requests",
                "expected": dimension.ResourceRequestsMetrics,
            },
            {
                "dimension": "app",
                "metrics": "requests",
                "expected": dimension.AppRequestsMetrics,
            },
            {
                "dimension": "resource_non200_status",
                "metrics": "requests",
                "expected": dimension.ResourceNon200StatusRequestsMetrics,
            },
        ]
        for test in data:
            result = dimension.DimensionMetricsFactory.create_dimension_metrics(
                DimensionEnum(test["dimension"]),
                MetricsEnum(test["metrics"]),
            )
            assert isinstance(result, test["expected"])
