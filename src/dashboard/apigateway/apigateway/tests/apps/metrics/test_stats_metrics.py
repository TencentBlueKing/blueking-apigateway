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

from apigateway.apps.metrics import stats_metrics


class TestStatisticsAPIRequestMetrics:
    @pytest.mark.parametrize(
        "step, expected",
        [
            (
                "5m",
                (
                    "sum(increase(bk_apigateway_apigateway_api_requests_total{}[5m])) "
                    "by (api_name, stage_name, resource_name, proxy_error)"
                ),
            )
        ],
    )
    def test_get_query_promql(self, mocker, step, expected):
        mocker.patch("apigateway.apps.metrics.dimension_metrics.BaseDimensionMetrics.default_labels", return_value=[])

        metrics = stats_metrics.StatisticsAPIRequestMetrics()
        result = metrics._get_query_promql(step)
        assert result == expected


class TestStatisticsAPIRequestDurationMetrics:
    @pytest.mark.parametrize(
        "step, expected",
        [
            (
                "5m",
                (
                    "sum(increase(bk_apigateway_apigateway_api_request_duration_milliseconds_sum{}[5m])) "
                    "by (api_name, stage_name, resource_name)"
                ),
            )
        ],
    )
    def test_get_query_promql(self, mocker, step, expected):
        mocker.patch("apigateway.apps.metrics.dimension_metrics.BaseDimensionMetrics.default_labels", return_value=[])

        metrics = stats_metrics.StatisticsAPIRequestDurationMetrics()
        result = metrics._get_query_promql(step)
        assert result == expected


class TestStatisticsAppRequestMetrics:
    @pytest.mark.parametrize(
        "step, expected",
        [
            (
                "5m",
                (
                    "sum(increase(bk_apigateway_apigateway_app_requests_total{}[5m])) "
                    "by (app_code, api_name, stage_name, resource_name)"
                ),
            )
        ],
    )
    def test_get_query_promql(self, mocker, step, expected):
        mocker.patch("apigateway.apps.metrics.dimension_metrics.BaseDimensionMetrics.default_labels", return_value=[])

        metrics = stats_metrics.StatisticsAppRequestMetrics()
        result = metrics._get_query_promql(step)
        assert result == expected


class TestStatisticsAppRequestByResourceMetrics:
    @pytest.mark.parametrize(
        "step, expected",
        [
            (
                "5m",
                (
                    "sum(increase(bk_apigateway_apigateway_app_requests_total{}[5m])) "
                    "by (app_code, api_name, resource_name)"
                ),
            )
        ],
    )
    def test_get_query_promql(self, mocker, step, expected):
        mocker.patch("apigateway.apps.metrics.dimension_metrics.BaseDimensionMetrics.default_labels", return_value=[])

        metrics = stats_metrics.StatisticsAppRequestByResourceMetrics()
        result = metrics._get_query_promql(step)
        assert result == expected
