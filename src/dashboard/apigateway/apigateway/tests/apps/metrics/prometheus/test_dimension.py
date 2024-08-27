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
from apigateway.apps.metrics.constants import MetricsEnum
from apigateway.apps.metrics.prometheus import dimension


class TestRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
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
                    "stage_id": 1,
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


class TestResponseTime90thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.9, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", resource_name="get_foo"}[1m])) by (le, api_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.9, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, api_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime90thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResponseTime50thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
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
                    "stage_id": 1,
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
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
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
                    "stage_id": 1,
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


class TestAppRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
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
                    "stage_id": 1,
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


class TestNon200StatusMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo", status!="200"}[1m])) by (api_name, status))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status!="200"}[1m])) by (api_name, status))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.Non200StatusMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestMetricsFactory:
    def test_create_metrics(self):
        data = [
            {
                "metrics": "requests",
                "expected": dimension.RequestsMetrics,
            },
            {
                "metrics": "requests_total",
                "expected": dimension.RequestTotalMetrics,
            },
            {
                "metrics": "non_200_status",
                "expected": dimension.Non200StatusMetrics,
            },
            {
                "metrics": "app_requests",
                "expected": dimension.AppRequestsMetrics,
            },
            {
                "metrics": "resource_requests",
                "expected": dimension.ResourceRequestsMetrics,
            },
            {
                "metrics": "response_time_50th",
                "expected": dimension.ResponseTime50thMetrics,
            },
            {
                "metrics": "response_time_80th",
                "expected": dimension.ResponseTime80thMetrics,
            },
            {
                "metrics": "response_time_90th",
                "expected": dimension.ResponseTime90thMetrics,
            },
            {
                "metrics": "ingress_space",
                "expected": dimension.IngressSpaceMetrics,
            },
            {
                "metrics": "egress_space",
                "expected": dimension.EgressSpaceMetrics,
            },
        ]
        for test in data:
            result = dimension.MetricsFactory.create_metrics(
                MetricsEnum(test["metrics"]),
            )
            assert isinstance(result, test["expected"])
