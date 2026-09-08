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
import json
from unittest.mock import call

from apigateway.biz.mcp_server_log.chain_query import search_chain_by_any_id
from apigateway.biz.mcp_server_log.chain_search import MCPServerLogChainSearchClient
from apigateway.biz.mcp_server_log.es_query import search_all_layers
from apigateway.biz.mcp_server_log.gateway_log import search_gateway_log
from apigateway.biz.mcp_server_log.log_search import MCPServerLogSearchClient


def test_search_chain_by_any_id_keeps_gateway_scope_for_fallbacks(mocker):
    request_client = mocker.MagicMock()
    request_client.search_chain.return_value = {"spans": []}
    x_request_client = mocker.MagicMock()
    x_request_client.search_chain_by_x_request_id.return_value = {"spans": []}
    upstream_client = mocker.MagicMock()
    upstream_client.search_chain_by_upstream_request_id.return_value = {"spans": [{"id": "span"}]}
    client_class = mocker.patch(
        "apigateway.biz.mcp_server_log.chain_query.MCPServerLogChainSearchClient",
        side_effect=[request_client, x_request_client, upstream_client],
    )

    result = search_chain_by_any_id("request-id", gateway_id=123)

    assert result["spans"]
    assert client_class.call_args_list == [
        call(request_id="request-id", gateway_id=123),
        call(x_request_id="request-id", gateway_id=123),
        call(upstream_request_id="request-id", gateway_id=123),
    ]


def test_search_all_layers_filters_gateway_id(mocker):
    es_client = mocker.MagicMock()
    es_client.execute_search.return_value = {"hits": {"hits": []}}

    search_all_layers(es_client, "timestamp", request_id="request-id", gateway_id=123)

    query = json.dumps(es_client.execute_search.call_args.args[0])
    assert '"gateway_id": 123' in query
    assert '"__ext_json.gateway_id": 123' in query
    assert '"__ext_json.gateway_id": "123"' in query


def test_search_gateway_log_filters_upstream_gateway(mocker):
    log_client = mocker.patch("apigateway.biz.mcp_server_log.gateway_log.LogSearchClient")
    log_client.return_value.search_logs.return_value = (0, [])

    search_gateway_log("request-id", gateway_id=123)

    log_client.assert_called_once_with(
        request_id="request-id",
        gateway_id=123,
        time_range=7 * 24 * 60 * 60,
    )


def test_upstream_request_fallback_does_not_query_gateway_log_without_scoped_mcp_log(mocker):
    mocker.patch("apigateway.biz.mcp_server_log.chain_search.BKLogESClient")
    mocker.patch(
        "apigateway.biz.mcp_server_log.chain_search.search_by_upstream_request_id",
        return_value=[],
    )
    search_gateway = mocker.patch("apigateway.biz.mcp_server_log.chain_search.search_gateway_log")
    client = MCPServerLogChainSearchClient(upstream_request_id="request-id", gateway_id=123)

    result = client.search_chain_by_upstream_request_id()

    assert result["spans"] == []
    assert result["downstream_gateway_log"] is None
    search_gateway.assert_not_called()


def test_upstream_request_fallback_queries_gateway_log_without_gateway_scope(mocker):
    mocker.patch("apigateway.biz.mcp_server_log.chain_search.BKLogESClient")
    mocker.patch(
        "apigateway.biz.mcp_server_log.chain_search.search_by_upstream_request_id",
        return_value=[],
    )
    search_gateway = mocker.patch(
        "apigateway.biz.mcp_server_log.chain_search.search_gateway_log",
        return_value={"request_id": "request-id"},
    )
    client = MCPServerLogChainSearchClient(upstream_request_id="request-id")

    result = client.search_chain_by_upstream_request_id()

    assert result["downstream_gateway_log"] == {"request_id": "request-id"}
    search_gateway.assert_called_once_with("request-id", gateway_type="downstream")


def test_log_search_reuses_gateway_filter_helper(mocker):
    mocker.patch("apigateway.biz.mcp_server_log.log_search.BKLogESClient")

    query = json.dumps(MCPServerLogSearchClient(gateway_id=123)._build_base_search().to_dict())
    assert '"gateway_id": 123' in query
    assert '"__ext_json.gateway_id": "123"' in query
