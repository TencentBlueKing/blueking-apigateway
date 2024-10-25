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

from apigateway.apps.metrics.constants import MetricsInstantEnum, MetricsRangeEnum
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
                    "resource_id": 1,
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
                    "resource_id": 1,
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


class TestNon200StatusMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo", status!="200"}[1m])) by (status))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status!="200"}[1m])) by (status))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.Non200StatusMetrics()
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
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_app_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo"}[1m])) by (app_code))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_app_requests_total{api_name="foo", '
                    'stage_name="prod"}[1m])) by (app_code))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.AppRequestsMetrics()
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
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo"}[1m])) by (resource_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod"}[1m])) by (resource_name))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResourceRequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResponseTime90thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.9, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", resource_name="get_foo"}[1m])) by (le, resource_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.9, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, resource_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime90thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestIngressMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 2,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_bandwidth{type="ingress", service="foo.prod.stage-1", '
                    'route="foo.prod.2"}[1m])) by (route))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_bandwidth{type="ingress", service="foo.prod.stage-1"'
                    "}[1m])) by (route))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.IngressMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestEgressMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 2,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_bandwidth{type="egress", service="foo.prod.stage-1", '
                    'route="foo.prod.2"}[1m])) by (route))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_bandwidth{type="egress", service="foo.prod.stage-1"'
                    "}[1m])) by (route))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.EgressMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestRequestTotalMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_id": 1,
                    "stage_name": "prod",
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo"})'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": ('sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", ' 'stage_name="prod"})'),
            },
        ]
        for test in data:
            metrics = dimension.RequestsTotalMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"]


class TestHealthRateMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.apps.metrics.prometheus.dimension.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", resource_name="get_foo", status=~"5.."})'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status=~"5.."})'
                ),
            },
        ]
        for test in data:
            metrics = dimension.HealthRateMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestMetricsRangeFactory:
    def test_create_metrics(self):
        data = [
            {
                "metrics": "requests",
                "expected": dimension.RequestsMetrics,
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
                "metrics": "response_time_90th",
                "expected": dimension.ResponseTime90thMetrics,
            },
            {
                "metrics": "ingress",
                "expected": dimension.IngressMetrics,
            },
            {
                "metrics": "egress",
                "expected": dimension.EgressMetrics,
            },
        ]
        for test in data:
            result = dimension.MetricsRangeFactory.create_metrics(
                MetricsRangeEnum(test["metrics"]),
            )
            assert isinstance(result, test["expected"])


class TestMetricsInstantFactory:
    def test_create_metrics(self):
        data = [
            {
                "metrics": "requests_total",
                "expected": dimension.RequestsTotalMetrics,
            },
            {
                "metrics": "health_rate",
                "expected": dimension.HealthRateMetrics,
            },
        ]
        for test in data:
            result = dimension.MetricsInstantFactory.create_metrics(
                MetricsInstantEnum(test["metrics"]),
            )
            assert isinstance(result, test["expected"])


class TestBaseMetrics:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (None, 0),
            (
                {
                    "result": True,
                    "code": 200,
                    "message": "OK",
                    "data": {"metrics": [], "series": []},
                },
                0,
            ),
            (
                {
                    "result": True,
                    "code": 200,
                    "message": "OK",
                    "data": {
                        "metrics": [],
                        "series": [
                            {
                                "datapoints": [
                                    [None, 1708290000000],
                                    [5, 1727161200000],
                                    [22, 1727164800000],
                                    [26, 1727197200000],
                                    [26, 1727200800000],
                                ]
                            }
                        ],
                    },
                },
                26,
            ),
            (
                {
                    "result": True,
                    "code": 200,
                    "message": "OK",
                    "data": {
                        "metrics": [],
                        "series": [
                            {
                                "datapoints": [
                                    [4, 1708290000000],
                                    [5, 1727161200000],
                                    [22, 1727164800000],
                                    [26, 1727197200000],
                                    [None, 1727200800000],
                                ]
                            }
                        ],
                    },
                },
                22,
            ),
        ],
    )
    def test_get_data_differ_number(self, data, expected):
        result = dimension.get_data_differ_number(data)
        assert result == expected
