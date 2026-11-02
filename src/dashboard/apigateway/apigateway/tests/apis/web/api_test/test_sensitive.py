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
import shlex
from urllib.parse import quote

import pytest

from apigateway.apis.web.api_test.sensitive import DebugDataSanitizer, sanitize_history


@pytest.mark.parametrize("secret", ["personal-token", "token'with\"quotes", "token+with/slashes="])
def test_scrub_echoes_and_curl_body(secret):
    sanitizer = DebugDataSanitizer()
    sanitizer.add_headers({"Authorization": f"Bearer {secret}"})
    body = json.dumps({"echo": secret, "ordinary": "value"})
    curl = shlex.join(["curl", "-H", f"Authorization: Bearer {secret}", "-d", body, "http://example.com"])
    result = sanitizer.clean_curl(curl)
    args = shlex.split(result)
    assert args[2] == "Authorization: ***"
    assert json.loads(args[4]) == {"echo": "***", "ordinary": "value"}
    assert sanitizer.clean(quote(secret, safe="")) == "***"


@pytest.mark.parametrize("secret", ['token"with\\quotes', "***", None])
@pytest.mark.parametrize("header_name", ["X-Bkapi-Authorization", "x-bkapi-authorization"])
def test_curl_preserves_non_sensitive_auth_fields_across_repeated_cleaning(secret, header_name):
    authorization = {"bk_app_code": "demo-app", "client_label": "中文标签"}
    if secret is not None:
        authorization["bk_app_secret"] = secret
    headers = {header_name: json.dumps(authorization)}
    sanitizer = DebugDataSanitizer()
    sanitizer.add_headers(headers)
    curl = shlex.join(["curl", "-H", f"{header_name}: {headers[header_name]}", "http://example.com"])
    expected = {"bk_app_code": "demo-app", "client_label": "中文标签"}
    if secret is not None:
        expected["bk_app_secret"] = "***"
    cleaned = sanitizer.clean_curl(curl)
    # The view cleans the whole response, then history reads clean the curl again.
    cleaned = sanitizer.clean({"curl": cleaned})["curl"]
    _, response = sanitize_history({}, {"data": {"curl": cleaned}})
    for result in [cleaned, response["data"]["curl"]]:
        header = shlex.split(result)[2]
        assert json.loads(header.partition(":")[2]) == expected
        assert "中文标签" in result


@pytest.mark.parametrize("value", ["invalid-json", "[]", "null", '"token"'])
def test_curl_masks_unparseable_or_non_object_auth_header(value):
    curl = shlex.join(["curl", "-H", f"X-Bkapi-Authorization: {value}", "http://example.com"])
    assert shlex.split(DebugDataSanitizer().clean_curl(curl))[2] == "X-Bkapi-Authorization: ***"


def test_json_redaction_preserves_readable_chinese():
    body = '{"message": "中文内容", "bk_token": "login-ticket"}'
    cleaned = DebugDataSanitizer().clean(body)
    assert json.loads(cleaned) == {"message": "中文内容", "bk_token": "***"}
    assert "中文内容" in cleaned


def test_cookie_values_and_json_escaped_echoes():
    sanitizer = DebugDataSanitizer()
    sanitizer.add_headers({"Cookie": "bk_token=cookie-token; session=session-token"})
    sanitizer.add_authorization({"bk_app_secret": 'secret"with-quotes'})
    clean = sanitizer.clean(
        {
            "body": json.dumps({"echo": 'secret"with-quotes', "cookies": "cookie-token/session-token"}),
            "headers": {"Set-Cookie": "bk_token=cookie-token", "X-Trace": "trace"},
        }
    )
    assert json.loads(clean["body"]) == {"echo": "***", "cookies": "***/session-token"}
    assert clean["headers"] == {"Set-Cookie": "***", "X-Trace": "trace"}


@pytest.mark.parametrize(
    "headers",
    [
        {"X-Bkapi-Authorization": json.dumps({"bk_app_secret": "old-app-secret", "access_token": "old-token"})},
        {"Authorization": "Bearer old-token"},
        {"Cookie": "bk_token=old-token"},
    ],
)
def test_history_removes_credentials_without_mutating_source(headers):
    request = {"headers": {**headers, "X-Trace": "trace"}, "body": "old-token", "query_params": {"page": "2"}}
    response = {
        "data": {
            "body": "old-token",
            "curl": shlex.join(
                [
                    "curl",
                    "-H",
                    f"{next(iter(headers))}: {next(iter(headers.values()))}",
                    "http://example.com",
                ]
            ),
        }
    }
    before = json.dumps([request, response])
    clean_request, clean_response = sanitize_history(request, response)
    assert clean_request["headers"] == {"X-Trace": "trace"}
    assert clean_request["query_params"] == {"page": "2"}
    assert "old-token" not in json.dumps([clean_request, clean_response])
    assert "old-app-secret" not in json.dumps([clean_request, clean_response])
    assert before == json.dumps([request, response])


def test_history_curl_without_request_headers():
    request, response = sanitize_history(
        {},
        {
            "data": {
                "curl": "curl -H 'Authorization: Bearer legacy-token' http://example.com",
                "body": "legacy-token",
            }
        },
    )
    assert "legacy-token" not in json.dumps(response)
    assert request == {"headers": {}}


def test_malformed_historical_curl_is_not_returned():
    _, response = sanitize_history({}, {"data": {"curl": "curl -H 'Authorization: Bearer token"}})
    assert response["data"]["curl"] == ""


def test_history_metadata_and_ordinary_cookies_are_preserved():
    request, response = sanitize_history(
        {"request_method": "GET", "type": "HTTP", "headers": {"Cookie": "bk_token=GET; foo=1"}},
        {"data": {"body": '{"value": 123, "echo": "GET"}'}},
    )
    assert request["request_method"] == "GET"
    assert request["type"] == "HTTP"
    assert json.loads(response["data"]["body"]) == {"value": 123, "echo": "***"}


def test_json_body_semantics_and_format_are_preserved_without_credentials():
    body = '{"foo":  1, "language": "zh-cn"}'
    sanitizer = DebugDataSanitizer()
    sanitizer.add_headers({"Cookie": "foo=1; blueking_language=zh-cn"})
    assert sanitizer.clean(body) == body


def test_custom_login_cookie_name_is_sensitive(settings):
    settings.BK_LOGIN_TICKET_KEY_TO_COOKIE_NAME = {"bk_ticket": "custom_login_ticket"}
    sanitizer = DebugDataSanitizer()
    sanitizer.add_headers({"Cookie": "custom_login_ticket=custom-ticket; theme=dark"})
    assert sanitizer.clean("custom-ticket and dark") == "*** and dark"


def test_response_authentication_headers_are_always_masked():
    sanitizer = DebugDataSanitizer()
    assert sanitizer.clean(
        {
            "headers": {
                "Set-Cookie": "session=newly-issued-session",
                "Authorization": "Bearer new-token",
                "X-Trace": "trace",
            }
        }
    ) == {"headers": {"Set-Cookie": "***", "Authorization": "***", "X-Trace": "trace"}}
