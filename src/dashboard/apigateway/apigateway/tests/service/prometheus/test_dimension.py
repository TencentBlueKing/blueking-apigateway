# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

import apigateway.service.prometheus as dimension
from apigateway.apps.metrics.constants import MetricsInstantEnum, MetricsRangeEnum


class TestRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo"}[1m]))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "backend_name": None,
                    "step": "1m",
                },
                "expected": (
                    'sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", stage_name="prod"}[1m]))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.RequestsMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"]


class TestNon20XStatusMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo", '
                    'status=~"3..|4..|5.."}[1m])) by (status))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", status=~"3..|4..|5.."}[1m])) by (status))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.Non20XStatusMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestAppRequestsMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_app_requests_total{api_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo"}[1m])) by (app_code))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
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
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(increase(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo"}[1m])) by (resource_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
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
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.9, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", backend_name="default", '
                    'resource_name="get_foo"}[1m])) by (le, resource_name))'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
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


class TestResponseTime50thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.5, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", backend_name="default", resource_name="get_foo"'
                    "}[1m])) by (le, resource_name))"
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.5, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, resource_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime50thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResponseTime95thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.95, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", backend_name="default", resource_name="get_foo"'
                    "}[1m])) by (le, resource_name))"
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.95, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, resource_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime95thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestResponseTime99thMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.99, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod", backend_name="default", resource_name="get_foo"'
                    "}[1m])) by (le, resource_name))"
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    "histogram_quantile(0.99, sum(rate(bk_apigateway_apigateway_api_request_duration_milliseconds_bucket{"
                    'api_name="foo", stage_name="prod"}[1m])) '
                    "by (le, resource_name))"
                ),
            },
        ]
        for test in data:
            metrics = dimension.ResponseTime99thMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result


class TestIngressMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])
        backend_filter = mocker.patch("apigateway.core.models.Backend.objects.filter")

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 2,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(rate(bk_apigateway_bandwidth{type="ingress", gateway_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo"}[1m])) '
                    "by (resource_name))"
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod-123456789",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(rate(bk_apigateway_bandwidth{type="ingress", gateway_name="foo", '
                    'stage_name="prod-123456789"}[1m])) by (resource_name))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.IngressMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result

        backend_filter.assert_not_called()


class TestEgressMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])
        backend_filter = mocker.patch("apigateway.core.models.Backend.objects.filter")

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 2,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(rate(bk_apigateway_bandwidth{type="egress", gateway_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo"}[1m])) '
                    "by (resource_name))"
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod-123456789",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": (
                    'topk(10, sum(rate(bk_apigateway_bandwidth{type="egress", gateway_name="foo", '
                    'stage_name="prod-123456789"}[1m])) by (resource_name))'
                ),
            },
        ]
        for test in data:
            metrics = dimension.EgressMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"], result

        backend_filter.assert_not_called()


class TestRequestTotalMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_id": 1,
                    "stage_name": "prod",
                    "backend_name": "default",
                    "resource_id": 1,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo"})'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
                    "stage_id": 1,
                    "resource_id": 1,
                    "resource_name": None,
                    "step": "1m",
                },
                "expected": ('sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", stage_name="prod"})'),
            },
        ]
        for test in data:
            metrics = dimension.RequestsTotalMetrics()
            result = metrics._get_query_promql(**test["params"])
            assert result == test["expected"]


class TestHealthRateMetrics:
    def test_get_query_promql(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        data = [
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": "default",
                    "stage_id": 1,
                    "resource_id": 0,
                    "resource_name": "get_foo",
                    "step": "1m",
                },
                "expected": (
                    'sum(bk_apigateway_apigateway_api_requests_total{api_name="foo", '
                    'stage_name="prod", backend_name="default", resource_name="get_foo", status=~"5.."})'
                ),
            },
            {
                "params": {
                    "gateway_name": "foo",
                    "stage_name": "prod",
                    "backend_name": None,
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


class TestLLMMetrics:
    def test_get_query_promql_with_resource_and_backend(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])
        backend_filter = mocker.patch("apigateway.core.models.Backend.objects.filter")

        params = {
            "gateway_name": "foo",
            "stage_name": "prod",
            "backend_name": "default",
            "stage_id": 1,
            "resource_id": 2,
            "resource_name": "chat_completions",
            "step": "1m",
        }

        latency = dimension.LLMLatencyAvgMetrics()._get_query_promql(**params)
        assert "llm_latency_sum" in latency
        assert "llm_latency_count" in latency
        assert "by (request_type)" in latency
        assert 'gateway_name="foo"' in latency
        assert 'stage_name="prod"' in latency
        assert 'backend_name="default"' in latency
        assert 'resource_name="chat_completions"' in latency
        assert "route_id" not in latency
        assert "service_id" not in latency

        tokens = dimension.LLMTokenUsageMetrics()._get_query_promql(**params)
        assert "llm_prompt_tokens" in tokens
        assert "llm_completion_tokens" in tokens
        assert '"token_type", "prompt"' in tokens
        assert '"token_type", "completion"' in tokens

        connections = dimension.LLMActiveConnectionsMetrics()._get_query_promql(**params)
        assert "llm_active_connections" in connections
        assert "sum by (request_type)" in connections

        backend_filter.assert_not_called()

    def test_get_query_promql_without_resource_or_backend(self, mocker):
        mocker.patch("apigateway.service.prometheus.BaseMetrics.default_labels", return_value=[])

        result = dimension.LLMLatencyAvgMetrics()._get_query_promql(
            gateway_name="foo",
            stage_name="prod",
            backend_name=None,
            stage_id=1,
            resource_id=0,
            resource_name=None,
            step="1m",
        )

        assert 'gateway_name="foo"' in result
        assert 'stage_name="prod"' in result
        assert "backend_name" not in result
        assert "resource_name" not in result
        assert "route_id" not in result
        assert "service_id" not in result


class TestMetricsRangeFactory:
    def test_create_metrics(self):
        data = [
            {
                "metrics": "requests",
                "expected": dimension.RequestsMetrics,
            },
            {
                "metrics": "non_20x_status",
                "expected": dimension.Non20XStatusMetrics,
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
            {
                "metrics": "llm_latency_avg",
                "expected": dimension.LLMLatencyAvgMetrics,
            },
            {
                "metrics": "llm_token_usage",
                "expected": dimension.LLMTokenUsageMetrics,
            },
            {
                "metrics": "llm_active_connections",
                "expected": dimension.LLMActiveConnectionsMetrics,
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
