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
from urllib.parse import parse_qsl, unquote_plus, urlencode

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


@pytest.mark.parametrize("field", ["body", "response_body"])
@pytest.mark.parametrize("serialized", [False, True])
@pytest.mark.parametrize("container", ["array", "array_data", "object_data"])
def test_recognizable_nested_json_strings_are_masked_without_changing_representation(field, serialized, container):
    embedded = json.dumps({"bk_token": "fixture-credential", "id": 1})
    payload = {"array": [embedded], "array_data": [{"data": embedded}], "object_data": {"data": embedded}}[container]
    original = {field: json.dumps(payload) if serialized else payload}
    saved = copy.deepcopy(original)
    scrubber = DataScrubber()
    result = scrubber.scrub_sensitive_data([original])[0]
    assert "fixture-credential" not in json.dumps(result)
    body = json.loads(result[field]) if serialized else result[field]
    text = body[0] if container == "array" else body[0]["data"] if container == "array_data" else body["data"]
    assert isinstance(text, str)
    assert json.loads(text) == {"bk_token": "***", "id": 1}
    assert scrubber.scrub_sensitive_data([result])[0] == result
    assert original == saved


def test_nested_json_strings_in_forms_are_masked():
    original = {"body": urlencode({"data": json.dumps({"bk_token": "fixture-credential", "id": 1})})}
    result = DataScrubber().scrub_sensitive_data([original])[0]
    assert json.loads(dict(parse_qsl(result["body"]))["data"]) == {"bk_token": "***", "id": 1}


def test_nested_json_string_decode_budget_fails_closed():
    text = json.dumps({"bk_token": "fixture-credential"})
    for _ in range(6):
        text = json.dumps(text)
    result = DataScrubber().scrub_sensitive_data([{"body": [text]}])[0]
    assert result["body"] == HIDDEN


@pytest.mark.parametrize(
    "fragment",
    [
        '{"token":"fixture-credential',
        ' { "token": "fixture-credential',
        '[{"token":"fixture-credential',
        '["fixture-credential',
        '[null, "fixture-credential',
        '[1, "fixture-credential',
        '"{\\"token\\":\\"fixture-credential',
    ],
)
@pytest.mark.parametrize("nested_data", [False, True])
def test_credible_nested_json_fragments_fail_closed(fragment, nested_data):
    original = {"body": [{"data": fragment} if nested_data else fragment], "request_id": "req"}
    result = DataScrubber().scrub_sensitive_data([original])[0]
    assert result == {"body": HIDDEN, "request_id": "req"}


def test_ordinary_structure_prefixed_prose_is_preserved():
    payload = ["[WARN] retry", "{name} required", {"message": "[Beta] tool", "path": "dir/a.txt"}]
    original = {"body": payload}
    assert DataScrubber().scrub_sensitive_data([original])[0] == original


@pytest.mark.parametrize("field", ["body", "body_param", "request_body", "response_body"])
@pytest.mark.parametrize(
    "text",
    [
        '<html><input name="token" value="fixture-credential"></html>',
        '<item token="fixture-credential"/>',
        "Authorization: Bearer token=fixture-credential",
        "Content-Type: text/plain; token=fixture-credential",
        "message=fixture-credential with spaces",
        "value=fixture-credential/path",
        "value=fixture-credential\n",
        "=fixture-credential",
        "token=fixture-credential&",
    ],
)
def test_equals_does_not_make_unknown_text_a_supported_form(field, text):
    result = DataScrubber().scrub_sensitive_data([{field: text}])[0]
    assert result[field] == HIDDEN
    assert "fixture-credential" not in unquote_plus(json.dumps(result))


def test_strict_form_preserves_encoded_values_and_business_field_names():
    value = "request=GET&response=ok&query=hello&result=success&message=hello+world&url=%2Fdemo%3Fa%3D1&token=x"
    result = DataScrubber().scrub_sensitive_data([{"body": value}])[0]
    assert parse_qsl(result["body"]) == [
        ("request", "GET"),
        ("response", "ok"),
        ("query", "hello"),
        ("result", "success"),
        ("message", "hello world"),
        ("url", "/demo?a=1"),
        ("token", "***"),
    ]


@pytest.mark.parametrize("field", ["body", "params", "request", "response", "result"])
@pytest.mark.parametrize("serialized", [False, True])
def test_business_json_carrier_names_preserve_ordinary_scalars(serialized, field):
    payload = {"query": "hello", "response": "ok", "result": "success", "request": "GET", "id": 1}
    payload["nested"] = {"params": "hello", "path": "dir/a.txt", "message": "[WARN] retry"}
    original = {field: json.dumps(payload) if serialized else payload}
    result = DataScrubber().scrub_sensitive_data([original])[0][field]
    assert (json.loads(result) if serialized else result) == payload


@pytest.mark.parametrize("serialized", [False, True])
def test_params_preserve_business_scalars_and_explicit_parameter_carriers(serialized):
    params = {
        "query": "hello",
        "response": "ok",
        "result": "success",
        "query_param": "token=fixture-credential&id=1",
        "header_param": '{"authorization":"fixture-credential"}',
        "path_param": '{"secret":"fixture-credential","id":42}',
        "body_param": '{"query":"hello","response":"ok","bk_token":"fixture-credential"}',
    }
    original = {"params": json.dumps(params) if serialized else params}
    result = DataScrubber().scrub_sensitive_data([original])[0]["params"]
    parsed = json.loads(result) if serialized else result
    assert {key: parsed[key] for key in ("query", "response", "result")} == {
        "query": "hello",
        "response": "ok",
        "result": "success",
    }
    assert parse_qsl(parsed["query_param"]) == [("token", "***"), ("id", "1")]
    assert json.loads(parsed["header_param"]) == {"authorization": "***"}
    assert json.loads(parsed["path_param"]) == {"secret": "***", "id": 42}
    assert json.loads(parsed["body_param"]) == {"query": "hello", "response": "ok", "bk_token": "***"}


def test_explicit_parameter_carriers_inside_business_body_are_scrubbed():
    original = {"body": {"nested": {"query": "hello", "query_param": "token=fixture-credential&id=1"}}}
    result = DataScrubber().scrub_sensitive_data([original])[0]["body"]["nested"]
    assert result["query"] == "hello"
    assert parse_qsl(result["query_param"]) == [("token", "***"), ("id", "1")]


def test_real_envelopes_and_nested_body_fields_still_fail_closed():
    payload = {
        "query": "hello",
        "response": "ok",
        "nested": {"body": "token=fixture-credential broken", "response_body": "fixture-credential"},
        "content": [{"type": "text", "text": "fixture-credential"}],
    }
    original = {"body": payload, "response": "fixture-credential", "query": "fixture-credential broken"}
    result = DataScrubber().scrub_sensitive_data([original])[0]
    assert result["body"] == {
        "query": "hello",
        "response": "ok",
        "nested": {"body": HIDDEN, "response_body": HIDDEN},
        "content": [{"type": "text", "text": HIDDEN}],
    }
    assert result["response"] == result["query"] == HIDDEN


@pytest.mark.parametrize("field", ["params", "query", "query_param"])
def test_explicit_query_allows_bare_flags_and_masks_credentials(field):
    result = DataScrubber().scrub_sensitive_data([{field: "debug&id=1&token=fixture-credential&debug"}])[0]
    assert parse_qsl(result[field], keep_blank_values=True) == [
        ("debug", ""),
        ("id", "1"),
        ("token", "***"),
        ("debug", ""),
    ]


@pytest.mark.parametrize("field", ["params", "query", "query_param"])
@pytest.mark.parametrize("value", ["debug&id=100%", "debug&token=%FF", "%ZZ&id=1"])
def test_explicit_query_flags_do_not_relax_percent_validation(field, value):
    assert DataScrubber().scrub_sensitive_data([{field: value}])[0][field] == HIDDEN


@pytest.mark.parametrize("kind", ["scrubber", "access", "mcp_list", "mcp_chain"])
def test_bounded_projected_json_previews_survive_repeated_dashboard_scrubbing(kind):
    projected_body = json.dumps(
        {
            "request_id": "req-body",
            "message": "[WARN] " + "x" * 32 + "...(truncated)",
            "data": json.dumps({"message": "{example} " + "y" * 32 + "...(truncated)", "bk_token": "***"}),
        }
    )
    projected_response_body = json.dumps({"id": 42, "message": "z" * 32 + "...(truncated)", "password": "***"})
    original = {
        "request_id": "req",
        "mcp_method": "tools/call",
        "body": projected_body,
        "params": json.dumps({"request_id": "req-params", "body": projected_body}),
        "response": json.dumps(
            {"request_id": "req-response", "status_code": 200, "response_body": projected_response_body}
        ),
    }
    saved = copy.deepcopy(original)
    scrubber = DataScrubber()
    hit = {"_source": original, "sort": [1700000000000]}
    if kind == "scrubber":
        result = scrubber.scrub_sensitive_data([original])[0]
    elif kind == "access":
        result = LogSearchClient(request_id="req")._to_log_display(hit)
    elif kind == "mcp_list":
        result = MCPServerLogSearchClient(request_id="req")._to_log_display(hit)
    else:
        result = _parse_hits([hit])[0]
    assert HIDDEN not in json.dumps(result, ensure_ascii=False)
    assert {key: result[key] for key in original} == original
    assert scrubber.scrub_sensitive_data([result])[0] == result
    assert json.loads(result["params"])["request_id"] == "req-params"
    assert json.loads(result["body"])["request_id"] == "req-body"
    response = json.loads(result["response"])
    assert response["request_id"] == "req-response"
    assert json.loads(response["response_body"])["id"] == 42
    assert original == saved
