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
from urllib.parse import parse_qsl

import pytest

from apigateway.biz.access_log import DataScrubber
from apigateway.biz.access_log.log_search import LogSearchClient
from apigateway.biz.mcp_server_log.es_query import _parse_hits
from apigateway.biz.mcp_server_log.log_search import MCPServerLogSearchClient

pytestmark = pytest.mark.no_meta_schema
HIDDEN = "正文已屏蔽：截断或格式未知，无法可靠脱敏"


def test_nested_mixed_body_keeps_fields_and_original():
    payload = [
        {
            "items": [[{"BK_APP_SECRET": {"value": "fixture-credential"}, "name": "demo"}]],
            "password": 0,
            "API_KEY": False,
            "bk_token": None,
            "client_secret": "",
        },
        2,
        None,
    ]
    original = {"body": json.dumps(payload), "response_body": payload, "request_id": "req"}
    saved = copy.deepcopy(original)
    result = DataScrubber().scrub_sensitive_data([original])[0]
    expected = [
        {
            "items": [[{"BK_APP_SECRET": "***", "name": "demo"}]],
            "password": "***",
            "API_KEY": "***",
            "bk_token": None,
            "client_secret": "",
        },
        2,
        None,
    ]
    assert json.loads(result["body"]) == expected
    assert result["response_body"] == expected
    assert result["request_id"] == "req"
    assert original == saved


@pytest.mark.parametrize(
    "body",
    [
        '{"bk_app_secr',
        '{"safe":"fixture-credential',
        '{"safe":"escaped\\',
        "text fixture-credential",
        "a=b&broken",
        "token=%ZZ",
        '"fixture-credential"',
    ],
)
@pytest.mark.parametrize("field", ["body", "response_body"])
def test_unknown_or_truncated_body_is_hidden_even_without_matching_key(body, field):
    assert DataScrubber().scrub_sensitive_data([{field: body}])[0][field] == HIDDEN


def test_headers_forms_and_additional_rules(settings):
    settings.LOG_SENSITIVE_KEYS = ["X-Custom-Auth"]
    value = {
        "header": '{"aUtHoRiZaTiOn":"fixture-credential", "X-Custom-Auth":["fixture-credential"]}',
        "params": "a=1&bk%5Ftoken=fixture-credential&a=2&bk_token=&password=0",
        "body": "a=1&bk_token=fixture-credential&a=2&bk_token=",
        "query": {"Cookie": "fixture-credential"},
        "path": {"client_secret": "fixture-credential"},
    }
    result = DataScrubber().scrub_sensitive_data([value])[0]
    assert json.loads(result["header"]) == {"aUtHoRiZaTiOn": "***", "X-Custom-Auth": "***"}
    assert parse_qsl(result["params"], keep_blank_values=True) == [
        ("a", "1"),
        ("bk_token", "***"),
        ("a", "2"),
        ("bk_token", ""),
        ("password", "***"),
    ]
    assert parse_qsl(result["body"], keep_blank_values=True) == [
        ("a", "1"),
        ("bk_token", "***"),
        ("a", "2"),
        ("bk_token", ""),
    ]
    assert result["query"] == {"Cookie": "***"}
    assert result["path"] == {"client_secret": "***"}


def test_envelope_and_sdk_text_sanitize_embedded_json():
    value = {
        "response": json.dumps(
            {"status_code": 200, "request_id": "req", "response_body": '{"bk_token":"fixture-credential"}'}
        ),
        "body": '{"response_body":"{\\"safe\\":\\"fixture-credential"}',
        "params": {"body": '{"bk_app_secret":"fixture-credential"}'},
        "request": '{"body": [{"api_key": ["fixture-credential"]}]}',
        "response_body": {
            "content": [
                {"type": "text", "text": '[{"secret":"fixture-credential"}]'},
                {"type": "text", "text": "fixture-credential"},
            ]
        },
    }
    result = DataScrubber().scrub_sensitive_data([value])[0]
    assert json.loads(result["response"]) == {
        "status_code": 200,
        "request_id": "req",
        "response_body": '{"bk_token": "***"}',
    }
    assert json.loads(result["body"])["response_body"] == HIDDEN
    assert result["params"]["body"] == '{"bk_app_secret": "***"}'
    assert json.loads(result["request"])["body"] == [{"api_key": "***"}]
    assert json.loads(result["response_body"]["content"][0]["text"]) == [{"secret": "***"}]
    assert result["response_body"]["content"][1]["text"] == HIDDEN
    assert "fixture-credential" not in json.dumps(result)


@pytest.mark.parametrize(
    "body", ['{"bk\\u005ftoken":"fixture-credential"}', '[{"authorization":"fixture-credential"}]']
)
def test_escaped_key_and_top_level_array(body):
    assert "fixture-credential" not in DataScrubber().scrub_sensitive_data([{"body": body}])[0]["body"]


def test_budgets_fail_closed():
    nested = {"bk_token": "fixture-credential"}
    for _ in range(40):
        nested = {"items": [nested]}
    encoded = {"bk_token": "fixture-credential"}
    for _ in range(8):
        encoded = {"body": json.dumps(encoded)}
    for value in [nested, json.dumps(nested), ' {"data":"' + "x" * (1024 * 1024) + '"}', encoded]:
        result = DataScrubber().scrub_sensitive_data([{"body": value}])[0]
        assert "fixture-credential" not in json.dumps(result)
        assert HIDDEN in str(result)


@pytest.mark.parametrize("kind", ["access", "mcp_list", "mcp_chain"])
def test_real_query_result_boundaries_sanitize_ext_copies(mocker, kind):
    source = {
        "request_id": "req",
        "mcp_method": "tools/call",
        "body": '{"bk_token":"fixture-credential"}',
        "response": '{"status_code":200,"response_body":"fixture-credential"}',
        "__ext_json": {
            "headers": {"authorization": "fixture-credential"},
            "params": '{"client_secret":"fixture-credential"}',
        },
        "http_path": "/demo",
        "tool_name": "demo",
    }
    hit = {"_source": source, "sort": [1700000000000]}
    saved = copy.deepcopy(hit)
    if kind == "mcp_chain":
        result = _parse_hits([hit])[0]
    else:
        module, cls = (
            ("access_log", LogSearchClient) if kind == "access" else ("mcp_server_log", MCPServerLogSearchClient)
        )
        mocker.patch(f"apigateway.biz.{module}.log_search.BKLogESClient").return_value.execute_search.return_value = {
            "hits": {"total": 1, "hits": [hit]}
        }
        total, logs = cls(request_id="req").search_logs()
        assert total == 1
        result = logs[0]
    assert "fixture-credential" not in json.dumps(result)
    assert result["request_id"] == "req"
    assert result["http_path"] == "/demo"
    assert result["tool_name"] == "demo"
    assert hit == saved


@pytest.mark.parametrize("field", ["body", "response_body", "params", "header"])
def test_budget_exhaustion_in_large_objects_and_cyclic_data(field):
    value = {"data": ["x" * 4096 for _ in range(300)], "bk_token": "fixture-credential"}
    assert DataScrubber().scrub_sensitive_data([{field: value}])[0][field] == HIDDEN
    value = []
    value.append(value)
    assert DataScrubber().scrub_sensitive_data([{field: value}])[0][field] == HIDDEN


def test_invalid_ext_json_and_nested_empty_values():
    result = DataScrubber().scrub_sensitive_data(
        [
            {
                "__ext_json": '{"bk_token":"fixture-credential',
                "body": {"password": [], "secret": {}, "credentials": "", "authorization": None},
                "http_path": "/demo",
                "response_body": "",
            }
        ]
    )[0]
    assert result["__ext_json"] == HIDDEN
    assert result["body"] == {"password": [], "secret": {}, "credentials": "", "authorization": None}
    assert result["response_body"] == ""
    assert result["http_path"] == "/demo"


def test_serialized_tool_path_parameters_and_http_path_metadata():
    result = DataScrubber().scrub_sensitive_data(
        [
            {"path": '{"client_secret":"fixture-credential","id":42}'},
            {"path": "/server/mcp", "__ext_json": {"path": '{"password":"fixture-credential"}'}},
        ]
    )
    assert json.loads(result[0]["path"]) == {"client_secret": "***", "id": 42}
    assert result[1]["path"] == "/server/mcp"
    assert json.loads(result[1]["__ext_json"]["path"]) == {"password": "***"}


def test_serialized_proxy_handler_fields_and_sdk_result():
    data = {
        "params": {
            "body_param": '{"bk_token":"fixture-credential"}',
            "query_param": "token=fixture-credential&keep=1&keep=2",
            "header_param": '{"authorization":"fixture-credential"}',
            "path_param": '{"secret":"fixture-credential"}',
        },
        "result": {"content": [{"type": "text", "text": "fixture-credential"}]},
    }
    result = DataScrubber().scrub_sensitive_data([data])[0]
    assert "fixture-credential" not in json.dumps(result)
    assert json.loads(result["params"]["body_param"]) == {"bk_token": "***"}
    assert parse_qsl(result["params"]["query_param"]) == [("token", "***"), ("keep", "1"), ("keep", "2")]
    assert result["result"]["content"][0]["text"] == HIDDEN


@pytest.mark.parametrize("field", ["body", "response_body", "params", "response"])
def test_serialized_null_preserves_its_representation(field):
    assert DataScrubber().scrub_sensitive_data([{field: "null"}])[0][field] == "null"


def test_exhausted_embedded_body_preserves_following_envelope_metadata():
    data = {
        "response": {
            "response_body": {"data": ["x" * 4096 for _ in range(300)]},
            "request_id": "req",
            "status_code": 502,
        }
    }
    result = DataScrubber().scrub_sensitive_data([data])[0]["response"]
    assert result == {"response_body": HIDDEN, "request_id": "req", "status_code": 502}
