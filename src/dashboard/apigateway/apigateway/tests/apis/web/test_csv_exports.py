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
import csv
import json
from copy import deepcopy
from io import StringIO

import pytest

from apigateway.apis.web.mcp_server.views import GatewayMCPServerAppPermissionExportApi
from apigateway.apis.web.metrics.views import QuerySummaryExportApi
from apigateway.apis.web.permission.views import AppPermissionExportApi

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("export_kind", ["access", "mcp"])
@pytest.mark.parametrize("user_agent", ["Windows", "Linux"])
@pytest.mark.parametrize(
    "value, expected",
    [
        ("=1+1", "'=1+1"),
        ("+1", "'+1"),
        ("-1", "'-1"),
        ("@sample", "'@sample"),
        ("  =1+1", "'  =1+1"),
        ("\t=1+1", "'\t=1+1"),
        ("\r\n+1", "'\r\n+1"),
        ("＝1+1", "'＝1+1"),
        ('=1+1,";\r\n@sample', "'=1+1,\";\r\n@sample"),
        ('中文,"引号"\r\n下一行', '中文,"引号"\r\n下一行'),
        ("plain =1+1", "plain =1+1"),
        ("", ""),
        (None, ""),
        (-42, "-42"),
        (-1.5, "-1.5"),
    ],
)
def test_log_csv_download(request_view, mocker, fake_stage, export_kind, user_agent, value, expected):
    text_fields = (
        ["http_path", "params", "body", "response_body", "app_code", "error"]
        if export_kind == "access"
        else ["tool_name", "prompt_name", "params", "response", "app_code", "error"]
    )
    if export_kind == "access" and isinstance(value, (int, float)):
        text_fields = ["status", "response_size"]
    log = dict.fromkeys(text_fields, value)
    # Preserve the access-log JSON contract and genuine numeric cells.
    log.update(llm_summary={"model": "=1+1", "中文": '"\n'})
    log.setdefault("status", 500)
    source = deepcopy(log)
    if export_kind == "access":
        mocker.patch("apigateway.apis.web.access_log.views.LogSearchClient.search_logs", return_value=(1, [log]))
    else:
        client = mocker.patch("apigateway.apis.web.mcp_server_log.views.build_mcp_server_log_client").return_value
        client.search_logs.return_value = (1, [log])

    response = request_view(
        "GET",
        "access_log.export" if export_kind == "access" else "mcp_server_log.export",
        path_params={"gateway_id": fake_stage.gateway.id},
        gateway=fake_stage.gateway,
        data={"stage_id": fake_stage.id, "time_start": 1720606081, "time_end": 1721210881},
        headers={"User-Agent": user_agent},
    )

    assert response.status_code == 200
    assert response.charset == ("utf-8-sig" if user_agent == "Windows" else "utf-8")
    rows = list(csv.DictReader(StringIO(b"".join(response.streaming_content).decode(response.charset))))
    assert len(rows) == 1
    for field in text_fields:
        assert rows[0][field] == expected
        assert log[field] == source[field]
    assert rows[0]["status"] == str(source["status"])
    if export_kind == "access":
        assert json.loads(rows[0]["llm_summary"]) == source["llm_summary"]


@pytest.mark.parametrize("value", ["=1+1", "+1", "-1", "@sample"])
@pytest.mark.parametrize("export_kind", ["metrics", "permissions", "mcp_permissions"])
def test_other_csv_exports(value, export_kind):
    if export_kind == "metrics":
        data = [{"stage_name": value, "resource_path": value, "bk_app_code": value, "total_count": -42}]
        content = QuerySummaryExportApi()._get_csv_content("gateway", 1, 2, data)
        fields = ["环境", "资源路径", "蓝鲸应用"]
    elif export_kind == "permissions":
        data = [{"bk_app_code": value, "resource_name": "resource", "resource_path": value}]
        content = AppPermissionExportApi()._get_csv_content(data)
        fields = ["蓝鲸应用ID", "请求路径"]
    else:
        data = [
            {
                "mcp_server": {"name": "server"},
                "bk_app_code": value,
                "applied_by": value,
                "handled_by": value,
                "effective_time": "永久",
                "grant_type": "grant",
            }
        ]
        content = GatewayMCPServerAppPermissionExportApi()._get_csv_content(data)
        fields = ["蓝鲸应用ID", "申请人", "审批人/授权人"]
    rows = list(csv.DictReader(StringIO(content)))
    assert len(rows) == 1
    for field in fields:
        assert rows[0][field] == "'" + value
    if export_kind == "metrics":
        assert rows[0]["请求总数"] == "-42"
