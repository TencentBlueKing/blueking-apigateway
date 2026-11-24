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
import copy
import json
from unittest.mock import MagicMock

import pytest

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "entry", ["access_list", "access_csv", "share", "toolbox", "open", "mcp_list", "mcp_csv", "mcp_chain"]
)
def test_log_credentials_at_public_outputs(entry, request_view, fake_stage, mocker):
    gateway = fake_stage.gateway
    source = {
        "request_id": "req",
        "mcp_method": "tools/call",
        "tool_name": "demo",
        "gateway_id": gateway.id,
        "body": '{"nested":[{"bk_app_secret":"fixture-credential"}]}',
        "params": '{"body":{"bk_token":"fixture-credential"}}'
        if entry.startswith("mcp")
        else "bk_token=fixture-credential",
        "response_body": '{"password":"fixture-credential"}',
        "response": '{"status_code":200,"response_body":"fixture-credential"}',
        "header": {"AUTHORIZATION": "fixture-credential"},
        "status": 200,
        "__ext_json": {"body": '{"bk_token":"fixture-credential"}'},
    }
    mocker.patch(
        "apigateway.service.es.BKLogESClient.execute_search",
        side_effect=lambda *args, **kwargs: {
            "hits": {"total": 1, "hits": [{"_source": copy.deepcopy(source), "sort": [1700000000000]}]}
        },
    )
    names = {
        "access_list": "access_log.logs",
        "access_csv": "access_log.export",
        "share": "access_log.logs.detail",
        "toolbox": "access_log.logs.query",
        "open": "openapi.v2.open.tools.log.query_by_request_id",
        "mcp_list": "mcp_server_log.logs",
        "mcp_csv": "mcp_server_log.export",
        "mcp_chain": "mcp_server_log.logs.chain",
    }
    paths = {"gateway_id": gateway.id}
    kwargs = {"gateway": gateway}
    data = {"time_range": 300, "time_start": 1700000000, "time_end": 1700000300, "stage_id": fake_stage.id}
    if entry in {"share", "mcp_chain"}:
        paths["request_id"] = "req"
        mocker.patch("apigateway.apis.web.access_log.views.SignatureValidator.is_valid")
    if entry == "toolbox":
        paths = {"request_id": "req"}
    if entry == "open":
        paths = {}
        data = {"request_id": "req"}
        kwargs = {"app": MagicMock(app_code="demo")}
    response = request_view("GET", names[entry], path_params=paths, data=data, **kwargs)
    assert response.status_code == 200
    content = b"".join(response.streaming_content).decode() if response.streaming else response.content.decode()
    assert "fixture-credential" not in content
    if entry.endswith("csv"):
        assert "***" in content
    else:
        result = response.json()["data"]
        assert "***" in json.dumps(result)
        assert "req" in json.dumps(result)
