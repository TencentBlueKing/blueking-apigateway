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
from copy import deepcopy

import pytest


@pytest.fixture
def chain_logs(mocker):
    logs = [
        {
            "request_id": "entry-gateway-id",
            "x_request_id": "trace-id",
            "upstream_request_id": "tool-gateway-id",
            "mcp_server_name": "example-server",
            "mcp_method": "tools/call",
            "tool_name": "example-tool",
            "latency": "10ms",
        }
    ]
    mocker.patch("apigateway.biz.mcp_server_log.chain_search.BKLogESClient")
    mocker.patch(
        "apigateway.biz.mcp_server_log.chain_search.search_all_layers",
        side_effect=lambda client, time_field, **ids: deepcopy(
            [log for log in logs if all(log.get(field) == value for field, value in ids.items())]
        ),
    )
    mocker.patch(
        "apigateway.biz.mcp_server_log.chain_search.search_by_upstream_request_id",
        side_effect=lambda client, time_field, request_id: deepcopy(
            [log for log in logs if log["upstream_request_id"] == request_id]
        ),
    )
    mocker.patch("apigateway.biz.mcp_server_log.chain_search.search_gateway_log", return_value=None)


@pytest.mark.parametrize(
    "view_name",
    ["mcp_server_log.logs.query", "mcp_server_log.logs.query.summary", "mcp_server_log.logs.query.chain"],
)
@pytest.mark.parametrize(
    "request_id, expected_count",
    [("entry-gateway-id", 1), ("tool-gateway-id", 1), ("trace-id", 0), ("missing-id", 0)],
)
def test_toolbox_queries_only_gateway_request_ids(request_view, chain_logs, view_name, request_id, expected_count):
    response = request_view("GET", view_name, path_params={"request_id": request_id})

    assert response.status_code == 200
    data = response.json()["data"]
    if view_name == "mcp_server_log.logs.query":
        assert data["count"] == len(data["results"]) == expected_count
        if expected_count:
            assert data["results"][0]["x_request_id"] == "trace-id"
    else:
        assert data["span_count"] == expected_count
        assert data["x_request_id"] == ("trace-id" if expected_count else "")


@pytest.mark.parametrize("view_name", ["mcp_server_log.logs.detail", "mcp_server_log.logs.chain"])
def test_management_keeps_trace_id_fallback(request_view, fake_gateway, chain_logs, view_name):
    response = request_view(
        "GET", view_name, path_params={"gateway_id": fake_gateway.id, "request_id": "trace-id"}, gateway=fake_gateway
    )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data.get("count", data.get("span_count")) == 1
    if "results" in data:
        assert data["results"][0]["x_request_id"] == "trace-id"
    else:
        assert data["x_request_id"] == "trace-id"
