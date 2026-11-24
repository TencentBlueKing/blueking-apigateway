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
from django.utils.translation import override

from apigateway.apis.web.mcp_server_metrics.serializers import (
    MCPServerMetricsQueryInstantInputSLZ,
    MCPServerMetricsQueryRangeInputSLZ,
)
from apigateway.apis.web.metrics.serializers import MetricsQueryInstantInputSLZ, MetricsQueryRangeInputSLZ


@pytest.fixture(
    params=[
        pytest.param((MetricsQueryRangeInputSLZ, "metrics.query_range", "dimension"), id="gateway-range"),
        pytest.param((MetricsQueryInstantInputSLZ, "metrics.query_instant", "dimension"), id="gateway-instant"),
        pytest.param(
            (MCPServerMetricsQueryRangeInputSLZ, "mcp_server_metrics.query_range", "mcp_server_dimension"),
            id="mcp-range",
        ),
        pytest.param(
            (MCPServerMetricsQueryInstantInputSLZ, "mcp_server_metrics.query_instant", "mcp_server_dimension"),
            id="mcp-instant",
        ),
    ]
)
def metrics_endpoint(request):
    return request.param


@pytest.mark.no_meta_schema
@pytest.mark.parametrize(
    "time_params, valid",
    [
        pytest.param({"time_range": 15552000}, True, id="relative-180-days"),
        pytest.param({"time_range": 15552001}, False, id="relative-over-limit-by-one-second"),
        pytest.param({"time_range": 315360000}, False, id="relative-ten-years"),
        pytest.param({"time_start": 100, "time_end": 15552100}, True, id="explicit-180-days"),
        pytest.param({"time_start": 100, "time_end": 15552101}, False, id="explicit-over-limit-by-one-second"),
        pytest.param({"time_start": 200, "time_end": 100}, False, id="reversed"),
        pytest.param({"time_start": 100, "time_end": 100}, True, id="equal-endpoints"),
        pytest.param({"time_start": 4102444800, "time_end": 4102444860}, True, id="future-policy-unchanged"),
        pytest.param(
            {"time_start": 100, "time_end": 200, "time_range": 315360000}, True, id="explicit-takes-priority"
        ),
        pytest.param(
            {"time_start": 200, "time_end": 100, "time_range": 60}, False, id="relative-cannot-hide-reversed"
        ),
        pytest.param(
            {"time_start": 100, "time_end": 15552101, "time_range": 60},
            False,
            id="relative-cannot-hide-long-explicit",
        ),
        pytest.param({"time_start": 100, "time_range": 15552001}, False, id="partial-explicit-long-relative"),
        pytest.param({"time_start": 100, "time_range": 60}, True, id="partial-explicit-relative-fallback"),
        pytest.param({"time_start": 0, "time_end": 200, "time_range": 60}, True, id="zero-start-relative-fallback"),
        pytest.param({"time_start": 0, "time_end": 200}, False, id="zero-start-without-relative"),
        pytest.param({"time_range": 0}, False, id="zero-relative"),
        pytest.param({}, False, id="missing-time"),
        pytest.param({"time_range": -1}, False, id="negative-relative"),
        pytest.param({"time_start": -1, "time_end": 100}, False, id="negative-start"),
        pytest.param({"time_range": "invalid"}, False, id="invalid-type"),
    ],
)
def test_serializer_time_range(metrics_endpoint, time_params, valid):
    serializer_class, view_name, _ = metrics_endpoint
    data = {"metrics": "requests_total" if view_name.endswith("instant") else "requests", **time_params}
    if view_name.startswith("metrics."):
        data["stage_id"] = 1
    serializer = serializer_class(data=data)

    assert serializer.is_valid() is valid, serializer.errors
    if valid:
        assert serializer.validated_data == data
    else:
        assert serializer.errors


@pytest.mark.no_meta_schema
@pytest.mark.parametrize("language", ["en", "zh-hans"])
@pytest.mark.parametrize(
    "time_params, english_error, chinese_error",
    [
        pytest.param(
            {"time_start": 200, "time_end": 100},
            "Parameter time_start cannot be later than time_end.",
            "参数 time_start 不能晚于 time_end。",
            id="reversed",
        ),
        pytest.param(
            {"time_range": 15552001},
            "The query time range cannot exceed 180 days.",
            "查询时间范围不可超过 180 天。",
            id="over-limit",
        ),
    ],
)
def test_time_range_error_translation(metrics_endpoint, language, time_params, english_error, chinese_error):
    serializer_class, view_name, _ = metrics_endpoint
    data = {"metrics": "requests_total" if view_name.endswith("instant") else "requests", **time_params}
    if view_name.startswith("metrics."):
        data["stage_id"] = 1

    with override(language):
        serializer = serializer_class(data=data)
        assert not serializer.is_valid()
        expected_error = english_error if language == "en" else chinese_error
        assert serializer.errors["non_field_errors"] == [expected_error]


@pytest.mark.parametrize(
    "time_params, status_code, expected_range",
    [
        pytest.param({"time_range": 15552000}, 200, (1754448000, 1770000000), id="relative-boundary"),
        pytest.param({"time_range": 15552001}, 400, None, id="relative-too-long"),
        pytest.param({"time_start": 100, "time_end": 15552100}, 200, (100, 15552100), id="explicit-boundary"),
        pytest.param({"time_start": 100, "time_end": 15552101}, 400, None, id="explicit-too-long"),
        pytest.param({"time_start": 200, "time_end": 100, "time_range": 60}, 400, None, id="reversed-with-relative"),
        pytest.param(
            {"time_start": 100, "time_end": 200, "time_range": 315360000}, 200, (100, 200), id="explicit-priority"
        ),
    ],
)
def test_api_validates_before_monitor_query(
    mocker, request_view, fake_stage, metrics_endpoint, time_params, status_code, expected_range
):
    _, view_name, monitor_module = metrics_endpoint
    monitor_query = mocker.patch(
        f"apigateway.service.prometheus.{monitor_module}.query_range", return_value={"series": []}
    )
    mocker.patch("apigateway.utils.time.now_timestamp", return_value=1770000000)
    data = {"metrics": "requests_total" if view_name.endswith("instant") else "requests", **time_params}
    if view_name.startswith("metrics."):
        data["stage_id"] = fake_stage.id
    if view_name.endswith("range"):
        data["step"] = "1m"

    response = request_view(
        "GET", view_name, path_params={"gateway_id": fake_stage.gateway.id}, gateway=fake_stage.gateway, data=data
    )

    assert response.status_code == status_code
    if expected_range is None:
        monitor_query.assert_not_called()
    else:
        monitor_query.assert_called_once()
        query = monitor_query.call_args.kwargs
        assert (query["start"], query["end"]) == expected_range
        if view_name.endswith("range"):
            assert query["step"] == "1m"
