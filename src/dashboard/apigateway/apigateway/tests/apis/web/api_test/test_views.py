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


import datetime
import json
import logging
import shlex
from html import unescape
from urllib.parse import quote, quote_plus, urlencode

import pytest
import requests
import responses
from ddf import G
from django.db import DatabaseError

from apigateway.apis.web.api_test import views
from apigateway.apis.web.api_test.data_models import ApiDebugHistoryRequest
from apigateway.apps.api_debug.models import APIDebugHistory
from apigateway.service.utils import get_resource_url
from apigateway.tests.utils.testing import dummy_time


class TestAPITestAPIView:
    @pytest.mark.parametrize("history_failure", [None, "database", "history_model"])
    @pytest.mark.parametrize("query_token", ["query-only-token", "query+token/with space="])
    def test_request_failure_does_not_expose_query_credentials(
        self,
        history_failure,
        query_token,
        settings,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource1,
        fake_released_resource,
        mocker,
        caplog,
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        history_secret = "history-only-secret"
        query_params = {"access_token": query_token, "page": "2"}
        send_request = mocker.patch(
            "apigateway.apis.web.api_test.views.requests.request",
            side_effect=requests.ConnectionError(f"request failed for http://example.com/?{urlencode(query_params)}"),
        )
        history_response = mocker.spy(views, "ApiDebugHistoryResponse")
        if history_failure == "database":
            create_history = mocker.patch.object(
                APIDebugHistory.objects, "create", side_effect=DatabaseError(f"storage failed with {history_secret}")
            )
        elif history_failure == "history_model":
            history_response = mocker.patch(
                "apigateway.apis.web.api_test.views.ApiDebugHistoryResponse",
                side_effect=ValueError(f"history model failed with {history_secret}"),
            )
            create_history = mocker.spy(APIDebugHistory.objects, "create")
        else:
            create_history = mocker.spy(APIDebugHistory.objects, "create")

        with caplog.at_level(logging.ERROR, logger="apigateway.apis.web.api_test.views"):
            response = request_view(
                "POST",
                "api_test.tests",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data={
                    "stage_id": fake_stage.id,
                    "resource_id": fake_resource1.id,
                    "method": "GET",
                    "headers": {},
                    "authorization": {},
                    "path_params": {},
                    "query_params": query_params,
                    "body": "",
                    "use_test_app": False,
                },
            )

        assert response.status_code == 500
        assert response.json()["error"]["code"] == "UNKNOWN"
        expected_error = "request failed for http://example.com/?access_token=***&page=2"
        assert expected_error in unescape(response.json()["error"]["message"])
        assert history_response.call_args.kwargs["error"] == expected_error
        send_request.assert_called_once()
        assert send_request.call_args.kwargs["params"] == query_params
        if history_failure == "history_model":
            create_history.assert_not_called()
        else:
            create_history.assert_called_once()
            assert create_history.call_args.kwargs["request"]["query_params"] == {"access_token": "***", "page": "2"}
            assert create_history.call_args.kwargs["response"]["error"] == expected_error
        if history_failure is None:
            history = APIDebugHistory.objects.get()
            assert history.response["error"] == expected_error
            assert history.request["query_params"] == {"access_token": "***", "page": "2"}
        else:
            assert not APIDebugHistory.objects.exists()
        for secret in (query_token, quote(query_token, safe=""), quote_plus(query_token), history_secret):
            assert secret not in response.content.decode()
            assert secret not in caplog.text
        if history_failure is None:
            return
        assert ("DatabaseError" if history_failure == "database" else "ValueError") in caplog.text
        assert "Failed to save API debug history" in caplog.text
        assert f"gateway_id={fake_gateway.id}" in caplog.text
        assert f"stage_id={fake_stage.id}" in caplog.text
        assert f"resource_id={fake_resource1.id}" in caplog.text
        assert query_token not in caplog.text
        assert history_secret not in caplog.text
        assert "ConnectionError" in caplog.text
        assert all(record.exc_info is None for record in caplog.records)

    @pytest.mark.parametrize("history_failure", [None, "database", "history_model"])
    @pytest.mark.parametrize("query_token", ["query-only-token", "query+token/with space="])
    @responses.activate
    def test_success_does_not_expose_query_credentials(
        self,
        history_failure,
        query_token,
        settings,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource1,
        fake_released_resource,
        mocker,
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        responses.add("GET", url, json={"echo": query_token, "page": "2"})
        history_response = mocker.spy(views, "ApiDebugHistoryResponse")
        if history_failure == "database":
            create_history = mocker.patch.object(
                APIDebugHistory.objects, "create", side_effect=DatabaseError("storage failed")
            )
        elif history_failure == "history_model":
            history_response = mocker.patch(
                "apigateway.apis.web.api_test.views.ApiDebugHistoryResponse",
                side_effect=ValueError("history model failed"),
            )
            create_history = mocker.spy(APIDebugHistory.objects, "create")
        else:
            create_history = mocker.spy(APIDebugHistory.objects, "create")
        query_params = {"access_token": query_token, "page": "2"}
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": "GET",
                "headers": {},
                "authorization": {},
                "path_params": {},
                "query_params": query_params,
                "body": "",
                "use_test_app": False,
            },
        )
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["status_code"] == 200
        assert json.loads(data["body"]) == {"echo": "***", "page": "2"}
        assert "access_token=***&page=2" in data["curl"]
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == f"{url}?{urlencode(query_params)}"
        assert history_response.call_args.kwargs["data"] == data
        assert history_response.call_args.kwargs["error"] is None
        if history_failure == "history_model":
            create_history.assert_not_called()
        else:
            create_history.assert_called_once()
            assert create_history.call_args.kwargs["response"]["data"] == data
        if history_failure is None:
            history = APIDebugHistory.objects.get()
            assert history.response["data"] == data
            assert history.request["query_params"] == {"access_token": "***", "page": "2"}
        else:
            assert not APIDebugHistory.objects.exists()
        for secret in (query_token, quote(query_token, safe=""), quote_plus(query_token)):
            assert secret not in response.content.decode()

    @pytest.mark.parametrize("failure", ["timeout", "connection", "invalid_json", "bad_response"])
    @pytest.mark.parametrize("history_unavailable", [False, True])
    def test_debug_failure_preserves_error(
        self,
        failure,
        history_unavailable,
        settings,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource1,
        fake_released_resource,
        mocker,
        caplog,
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        send_request = mocker.patch("apigateway.apis.web.api_test.views.requests.request")
        body = ""
        if failure == "invalid_json":
            body = "{invalid-json"
            expected_error = str(json.JSONDecodeError("Expecting property name enclosed in double quotes", body, 1))
        elif failure == "bad_response":
            send_request.return_value = object()
            expected_error = "'object' object has no attribute 'request'"
        else:
            exception = requests.Timeout if failure == "timeout" else requests.ConnectionError
            send_request.side_effect = exception("request failed <upstream> with personal-token")
            expected_error = "request failed <upstream> with ***"
        create_history = mocker.spy(APIDebugHistory.objects, "create")
        if history_unavailable:
            create_history = mocker.patch.object(
                APIDebugHistory.objects, "create", side_effect=DatabaseError("storage failed with personal-token")
            )
        with caplog.at_level(logging.ERROR, logger="apigateway.apis.web.api_test.views"):
            response = request_view(
                "POST",
                "api_test.tests",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data={
                    "stage_id": fake_stage.id,
                    "resource_id": fake_resource1.id,
                    "method": "GET",
                    "headers": {"Authorization": "Bearer personal-token"},
                    "path_params": {},
                    "query_params": {},
                    "body": body,
                    "use_test_app": False,
                },
            )
        assert response.status_code == 500
        assert response.json()["error"]["code"] == "UNKNOWN"
        message = response.json()["error"]["message"]
        assert "请求网关资源失败" in message
        assert expected_error in unescape(message)
        assert "<upstream>" not in message
        assert "storage failed" not in message
        assert "personal-token" not in response.content.decode()
        create_history.assert_called_once()
        recorded_response = create_history.call_args.kwargs["response"]
        assert recorded_response == {"data": None, "spec_version": 1, "error": expected_error}
        assert create_history.call_args.kwargs["request"]["headers"] == {}
        if failure == "invalid_json":
            send_request.assert_not_called()
        else:
            send_request.assert_called_once()
        if history_unavailable:
            assert not APIDebugHistory.objects.exists()
            assert expected_error not in caplog.text
            assert "DatabaseError" in caplog.text
            assert "personal-token" not in caplog.text
            assert all(record.exc_info is None for record in caplog.records)
        else:
            assert APIDebugHistory.objects.get().response == recorded_response

    @pytest.mark.parametrize("failure", ["database", "history_model"])
    @responses.activate
    def test_success_is_preserved_when_history_fails(
        self,
        failure,
        settings,
        request_view,
        fake_gateway,
        fake_stage,
        fake_resource1,
        fake_released_resource,
        mocker,
        caplog,
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        responses.add("GET", url, json={"message": "gateway responded"})
        if failure == "database":
            create_history = mocker.patch.object(
                APIDebugHistory.objects, "create", side_effect=DatabaseError("storage failed with personal-token")
            )
        else:
            # Pydantic validation failures may include the input data in their message.
            mocker.patch(
                "apigateway.apis.web.api_test.views.ApiDebugHistoryResponse",
                side_effect=ValueError("history model failed with personal-token"),
            )
            create_history = mocker.spy(APIDebugHistory.objects, "create")
        with caplog.at_level(logging.ERROR, logger="apigateway.apis.web.api_test.views"):
            response = request_view(
                "POST",
                "api_test.tests",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data={
                    "stage_id": fake_stage.id,
                    "resource_id": fake_resource1.id,
                    "method": "GET",
                    "headers": {"Authorization": "Bearer personal-token"},
                    "path_params": {},
                    "query_params": {},
                    "body": "",
                    "use_test_app": False,
                },
            )
        assert response.status_code == 200
        assert response.json()["data"]["status_code"] == 200
        assert json.loads(response.json()["data"]["body"]) == {"message": "gateway responded"}
        assert "personal-token" not in response.content.decode()
        assert len(responses.calls) == 1
        assert not APIDebugHistory.objects.exists()
        if failure == "database":
            create_history.assert_called_once()
            assert create_history.call_args.kwargs["response"]["error"] is None
            assert create_history.call_args.kwargs["response"]["data"] == response.json()["data"]
            assert "DatabaseError" in caplog.text
        else:
            create_history.assert_not_called()
            assert "ValueError" in caplog.text
        assert "personal-token" not in caplog.text
        assert all(record.exc_info is None for record in caplog.records)

    @pytest.mark.parametrize("source", ["body", "cookie"])
    @responses.activate
    def test_response_only_credentials_are_hidden_in_all_debug_representations(
        self, source, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        secret = "new-response-only-ticket"
        body = {"echo": secret, "nested": [{"echo": secret}], "count": 1}
        headers = {"Content-Type": "application/json", "X-Echo": f"issued: {secret}"}
        if source == "body":
            body["access_token"] = secret
        else:
            headers["Set-Cookie"] = f"bk_token={secret}; Path=/; HttpOnly"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        request_body = {"echo": secret, "name": "ordinary"}

        def respond(req):
            assert json.loads(req.body) == request_body
            return 200, headers, json.dumps(body)

        responses.add_callback("POST", url, callback=respond)
        result = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": "POST",
                "headers": {},
                "path_params": {},
                "query_params": {},
                "body": json.dumps(request_body),
                "use_test_app": False,
            },
        )
        assert result.status_code == 200, result.json()
        history = APIDebugHistory.objects.get()
        assert result.json()["data"] == history.response["data"]
        assert json.loads(history.request["body"]) == {"echo": "***", "name": "ordinary"}
        assert json.loads(history.response["data"]["body"])["count"] == 1
        assert secret not in json.dumps([history.request, history.response])
        assert secret not in result.content.decode()
        for detail in [False, True]:
            params = {"gateway_id": fake_gateway.id}
            if detail:
                params["id"] = history.id
            response = request_view(
                "GET",
                "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list",
                path_params=params,
                gateway=fake_gateway,
            )
            assert response.status_code == 200
            assert secret not in response.content.decode()

    @pytest.mark.parametrize("source", ["query", "body", "response_header"])
    @responses.activate
    def test_short_credentials_preserve_ordinary_debug_fields(
        self, source, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        request_body = {"password": "a", "echo": "a", "name": "application"} if source == "body" else {}
        query = {"token": "a", "name": "application"} if source == "query" else {}
        headers = {"Content-Type": "application/json"}
        if source == "response_header":
            headers["X-Token"] = "a"
        response_body = json.dumps({"echo": "a", "name": "application", "status": "active"})

        def respond(req):
            assert json.loads(req.body) == request_body
            assert req.url.startswith(url)
            if source == "query":
                assert "token=a" in req.url
            return 200, headers, response_body

        responses.add_callback("POST", url, callback=respond)
        result = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": "POST",
                "headers": {"Content-Type": "application/json"},
                "path_params": {},
                "query_params": query,
                "body": json.dumps(request_body),
                "use_test_app": False,
            },
        )
        assert result.status_code == 200, result.json()
        history = APIDebugHistory.objects.get()
        for data in [result.json()["data"], history.response["data"]]:
            assert json.loads(data["body"]) == {"echo": "***", "name": "application", "status": "active"}
            assert data["headers"]["Content-Type"] == "application/json"
            assert data["size"] == f"{len(response_body.encode()) / 1024:.2f}"
            args = shlex.split(data["curl"])
            assert args[0] == "curl"
            assert any(arg == "Content-Type: application/json" for arg in args)
            assert any(arg.startswith(url) for arg in args)
        assert history.request["request_url"] == url

    @pytest.mark.parametrize("fails", [False, True])
    @responses.activate
    def test_credential_headers_are_sent_but_hidden_from_history(
        self, fails, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource
    ):
        settings.API_RESOURCE_URL_TMPL = "http://example.com/{stage_name}/{resource_path}"
        authorization = {
            "bk_app_code": "debug-app",
            "nested": [{"BK_APP_SECRET": "nested-secret", "TOKEN": ["nested-token"]}, "ordinary", 1],
        }
        headers = {
            "cOoKiE": "bk_token=cookie-secret; theme=dark",
            "aUtHoRiZaTiOn": "Basic basic-secret",
            "pRoXy-AuThOrIzAtIoN": "Basic proxy-secret",
            "x-bKaPi-AuThOrIzAtIoN": json.dumps(authorization),
            "x-aPi-kEy": "api-key-secret",
            "x-aUtH-tOkEn": "auth-token-secret",
            "x-tOkEn": "token-secret",
            "x-aCcEsS-tOkEn": "access-token-secret",
            "X-Trace": "trace",
        }
        secrets = [
            "cookie-secret",
            "basic-secret",
            "proxy-secret",
            "nested-secret",
            "nested-token",
            "api-key-secret",
            "auth-token-secret",
            "token-secret",
            "access-token-secret",
        ]
        body = {"items": [{"PASSWORD": "body-password", "name": "ordinary"}], "body_echo": "body-password", "count": 1}
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)

        def respond(req):
            for name, value in headers.items():
                if name.lower() == "x-bkapi-authorization":
                    assert json.loads(req.headers[name]) == authorization
                else:
                    assert req.headers[name] == value
            assert json.loads(req.body) == body
            if fails:
                raise requests.ConnectionError("failed: " + "/".join(secrets))
            return (
                200,
                {"Content-Type": "application/json", "Authorization": "Bearer issued-secret", "X-Trace": "trace"},
                json.dumps({"echo": "/".join(secrets), "issued": "issued-secret", **body}),
            )

        responses.add_callback("POST", url, callback=respond)
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": "POST",
                "headers": headers,
                "path_params": {},
                "query_params": {"API_KEY": "query-secret", "page": "2"},
                "body": json.dumps(body),
                "use_test_app": False,
            },
        )
        assert len(responses.calls) == 1
        assert response.status_code == (500 if fails else 200), response.json()
        history = APIDebugHistory.objects.get()
        assert history.request["headers"] == {"X-Trace": "trace"}
        assert json.loads(history.request["body"]) == {
            "items": [{"PASSWORD": "***", "name": "ordinary"}],
            "body_echo": "***",
            "count": 1,
        }
        assert history.request["query_params"] == {"API_KEY": "***", "page": "2"}
        assert "authorization" not in history.request
        if not fails:
            assert response.json()["data"] == history.response["data"]
            assert json.loads(history.response["data"]["body"])["count"] == 1
        for payload in [response.content.decode(), json.dumps([history.request, history.response])]:
            for secret in [*secrets, "body-password", "query-secret", "issued-secret"]:
                assert secret not in payload
        for detail in [False, True]:
            params = {"gateway_id": fake_gateway.id}
            if detail:
                params["id"] = history.id
            result = request_view(
                "GET",
                "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list",
                path_params=params,
                gateway=fake_gateway,
            )
            assert result.status_code == 200
            for secret in [*secrets, "body-password", "query-secret", "issued-secret"]:
                assert secret not in result.content.decode()

    @pytest.mark.parametrize("mode", ["cookie", "ticket", "access_token", "bearer", "legacy_headers"])
    @responses.activate
    def test_authentication_and_sensitive_history(
        self, mode, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource, mocker
    ):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"
        fake_resource1.method = "GET"
        settings.DEFAULT_TEST_APP = {"bk_app_code": "debug-app", "bk_app_secret": "test-app-secret"}
        grant = mocker.patch(
            "apigateway.apis.web.api_test.views.ResourcePermissionHandler.grant_or_renewal_expire_soon"
        )
        headers = {"X-Trace": "trace"} | {
            "access_token": {"x-bkapi-authorization": json.dumps({"access_token": "access-token"})},
            "bearer": {"authorization": "Bearer personal-token"},
            "legacy_headers": {"X-Bkapi-Authorization": json.dumps({"uin": "12345", "skey": "legacy-skey"})},
        }.get(mode, {})
        authorization = {"bk_ticket": "login-ticket"} if mode == "ticket" else {}

        def respond(req):
            if mode == "bearer":
                assert "X-Bkapi-Authorization" not in req.headers
                assert req.headers["Authorization"] == "Bearer personal-token"
                auth = {}
            else:
                auth = json.loads(req.headers["X-Bkapi-Authorization"])
            if mode == "access_token":
                assert auth == {"access_token": "access-token"}
            elif mode != "bearer":
                assert auth["bk_app_code"] == "debug-app"
                assert auth["bk_app_secret"] == "test-app-secret"
                if mode == "ticket":
                    assert auth["bk_ticket"] == "login-ticket"
                elif mode == "cookie":
                    assert auth[settings.BK_LOGIN_TICKET_KEY]
                elif mode == "legacy_headers":
                    assert auth["uin"] == "12345"
                    assert auth["skey"] == "legacy-skey"
            body = json.dumps(dict(req.headers))
            return (
                200,
                {
                    "Content-Type": "application/json",
                    "Content-Length": str(len(body)),
                    "X-Echo": req.headers.get("Authorization", ""),
                },
                body,
            )

        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        responses.add_callback(fake_resource1.method, url, callback=respond)
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": fake_resource1.method,
                "headers": headers,
                "path_params": {},
                "query_params": {},
                "body": "",
                "use_test_app": True,
                "use_user_from_cookies": mode == "cookie",
                "authorization": authorization,
            },
        )
        assert response.status_code == 200, response.json()
        if mode in {"access_token", "bearer"}:
            grant.assert_not_called()
        else:
            grant.assert_called_once()
        history = APIDebugHistory.objects.get()
        assert history.request["headers"] == {"X-Trace": "trace"}
        assert response.json()["data"] == history.response["data"]
        if mode != "bearer":
            args = shlex.split(history.response["data"]["curl"])
            auth_header = next(arg for arg in args if arg.lower().startswith("x-bkapi-authorization:"))
            auth = json.loads(auth_header.partition(":")[2])
            if mode == "access_token":
                assert auth == {"access_token": "***"}
            else:
                assert auth["bk_app_code"] == "debug-app"
                assert auth["bk_app_secret"] == "***"
        for secret in ["test-app-secret", "login-ticket", "access-token", "personal-token", "legacy-skey"]:
            assert secret not in json.dumps(history.request)
            assert secret not in json.dumps(history.response)
            assert secret not in response.content.decode()
        assert len(responses.calls) == 1

    @pytest.mark.parametrize("secret", ['app"secret', "app\\secret", 'app"secret\\with-both'])
    @responses.activate
    def test_json_encoded_auth_header_echo_is_not_returned_or_stored(
        self, secret, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource
    ):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)

        def respond(req):
            assert json.loads(req.headers["X-Bkapi-Authorization"])["bk_app_secret"] == secret
            body = json.dumps({"echoed_headers": dict(req.headers)})
            return 200, {"Content-Type": "application/json", "Content-Length": str(len(body))}, body

        responses.add_callback("GET", url, callback=respond)
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": "GET",
                "headers": {},
                "path_params": {},
                "query_params": {},
                "body": "",
                "use_test_app": False,
                "authorization": {"bk_app_code": "demo", "bk_app_secret": secret},
            },
        )
        assert response.status_code == 200, response.json()
        history = APIDebugHistory.objects.get()
        for data in [response.json()["data"], history.response["data"]]:
            assert json.loads(data["body"])["echoed_headers"]["X-Bkapi-Authorization"] == "***"
        assert len(responses.calls) == 1

    @pytest.mark.parametrize("cookie", ["preferred_method=GET", "foo=1; blueking_language=zh-cn; theme=dark"])
    @responses.activate
    def test_ordinary_cookies_preserve_request_metadata_and_response(
        self, cookie, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource
    ):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        body = {"method": "GET", "number": 123, "language": "zh-cn", "message": "dark theme enabled"}
        responses.add("GET", url, json=body)
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": "GET",
                "headers": {"Cookie": cookie},
                "path_params": {},
                "query_params": {},
                "body": "",
                "use_test_app": False,
            },
        )
        assert response.status_code == 200, response.json()
        assert json.loads(response.json()["data"]["body"]) == body
        history = APIDebugHistory.objects.get()
        assert history.request["request_method"] == "GET"
        assert history.request["type"] == "HTTP"
        assert history.request["headers"] == {}
        assert json.loads(history.response["data"]["body"]) == body
        assert len(responses.calls) == 1

    @responses.activate
    def test_request_failure_does_not_expose_credentials(
        self, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource
    ):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"
        fake_resource1.method = "GET"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        responses.add(fake_resource1.method, url, body=requests.ConnectionError("failed with personal-token"))
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": fake_resource1.method,
                "headers": {"Authorization": "Bearer personal-token"},
                "path_params": {},
                "query_params": {},
                "body": "",
                "use_test_app": False,
            },
        )
        assert response.status_code == 500
        assert "personal-token" not in response.content.decode()
        history = APIDebugHistory.objects.get()
        assert history.request["headers"] == {}
        assert "personal-token" not in json.dumps(history.response)

    @responses.activate
    def test_post(self, settings, request_view, fake_gateway, fake_stage, fake_resource1, fake_released_resource):
        settings.API_RESOURCE_URL_TMPL = "http://bking.com/{stage_name}/{resource_path}"
        fake_resource1.method = "GET"
        url = get_resource_url(settings.API_RESOURCE_URL_TMPL, fake_gateway.name, fake_stage.name, fake_resource1.path)
        responses.add(
            fake_resource1.method,
            url,
            body="a" * 3000,
            adding_headers={
                "x-token": "test",
            },
            content_type="text/plain",
        )
        response = request_view(
            "POST",
            "api_test.tests",
            path_params={"gateway_id": fake_gateway.id},
            gateway=fake_gateway,
            data={
                "stage_id": fake_stage.id,
                "resource_id": fake_resource1.id,
                "method": fake_resource1.method,
                "headers": {},
                "path_params": {},
                "query_params": {},
                "body": "",
                "use_test_app": True,
            },
        )

        result = response.json()
        assert response.status_code == 200
        assert result["data"]["headers"] == {
            "Content-Type": "text/plain",
            "x-token": "***",
        }

        # 查看是否有记录
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id},
            view_name="api_debug.histories.list",
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) == 1


class TestAPIDebugHistoryApi:
    @pytest.mark.parametrize("detail", [False, True])
    @pytest.mark.parametrize("successful", [False, True])
    @pytest.mark.parametrize("query_token", ["legacy-query-token", "legacy+token/with space="])
    def test_masked_old_history_query_credentials_are_hidden(
        self, detail, successful, query_token, request_view, fake_gateway, fake_resource
    ):
        query_params = {"access_token": "***", "page": "2"}
        url = f"http://example.com/?{urlencode({'access_token': query_token, 'page': '2'})}"
        stored_response = (
            {"error": None, "data": {"curl": shlex.join(["curl", url]), "body": query_token}}
            if successful
            else {"error": f"request failed for {url}", "data": None}
        )
        history = G(
            APIDebugHistory,
            resource_name=fake_resource.name,
            gateway=fake_gateway,
            request={"headers": {}, "query_params": query_params},
            response=stored_response,
        )
        params = {"gateway_id": fake_gateway.id}
        if detail:
            params["id"] = history.id
        response = request_view(
            "GET", "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list", path_params=params
        )
        assert response.status_code == 200
        item = response.json()["data"] if detail else response.json()["data"][0]
        assert item["request"]["query_params"] == query_params
        if successful:
            assert "access_token=***&page=2" in item["response"]["data"]["curl"]
            assert item["response"]["data"]["body"] == "***"
        else:
            assert item["response"]["error"] == "request failed for http://example.com/?access_token=***&page=2"
        for value in (query_token, quote(query_token, safe=""), quote_plus(query_token)):
            assert value not in response.content.decode()
        history.refresh_from_db()
        assert history.request["query_params"] == query_params
        assert history.response == stored_response

    @pytest.mark.parametrize("detail", [False, True])
    def test_old_history_query_credentials_are_hidden(self, detail, request_view, fake_gateway, fake_resource):
        query_params = {"access_token": "old-query-token", "page": "2"}
        url = f"http://example.com/?{urlencode(query_params)}"
        history = G(
            APIDebugHistory,
            resource_name=fake_resource.name,
            gateway=fake_gateway,
            request={"headers": {}, "query_params": query_params},
            response={"error": f"request failed for {url}", "data": {"curl": shlex.join(["curl", url])}},
        )
        params = {"gateway_id": fake_gateway.id}
        if detail:
            params["id"] = history.id
        response = request_view(
            "GET", "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list", path_params=params
        )
        assert response.status_code == 200
        assert "old-query-token" not in response.content.decode()
        item = response.json()["data"] if detail else response.json()["data"][0]
        assert item["request"]["query_params"] == {"access_token": "***", "page": "2"}
        assert item["response"]["error"] == "request failed for http://example.com/?access_token=***&page=2"
        assert "access_token=***&page=2" in item["response"]["data"]["curl"]
        history.refresh_from_db()
        assert history.request["query_params"] == query_params
        assert history.response["error"] == f"request failed for {url}"

    @pytest.mark.parametrize("detail", [False, True])
    @pytest.mark.parametrize("request_url", [None, ""])
    def test_histories_preserve_empty_request_url(
        self, detail, request_url, request_view, fake_gateway, fake_resource
    ):
        history_request = ApiDebugHistoryRequest(
            request_url=request_url,
            headers={"Authorization": "Bearer legacy-history-ticket"},
            body=json.dumps({"echo": "issued-history-ticket", "name": "ordinary"}),
        ).model_dump()
        history = G(
            APIDebugHistory,
            gateway=fake_gateway,
            resource_name=fake_resource.name,
            request=history_request,
            response={
                "data": {
                    "body": json.dumps(
                        {"access_token": "issued-history-ticket", "echo": "issued-history-ticket", "count": 1}
                    )
                }
            },
        )
        normal_history = G(
            APIDebugHistory,
            gateway=fake_gateway,
            resource_name=fake_resource.name,
            request=ApiDebugHistoryRequest(request_url="http://example.com/ordinary").model_dump(),
            response={},
        )
        params = {"gateway_id": fake_gateway.id}
        if detail:
            params["id"] = history.id
        response = request_view(
            "GET",
            "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list",
            path_params=params,
            gateway=fake_gateway,
        )
        assert response.status_code == 200
        data = response.json()["data"]
        items = {item["id"]: item for item in ([data] if detail else data)}
        item = items[history.id]
        assert item["request"]["request_url"] == request_url
        assert item["request"]["headers"] == {}
        assert json.loads(item["request"]["body"]) == {"echo": "***", "name": "ordinary"}
        assert json.loads(item["response"]["data"]["body"]) == {"access_token": "***", "echo": "***", "count": 1}
        assert "legacy-history-ticket" not in response.content.decode()
        assert "issued-history-ticket" not in response.content.decode()
        if not detail:
            assert set(items) == {history.id, normal_history.id}
            assert items[normal_history.id]["request"]["request_url"] == "http://example.com/ordinary"
        history.refresh_from_db()
        assert history.request == history_request

    @pytest.mark.parametrize("detail", [False, True])
    @pytest.mark.parametrize("source", ["body", "cookie"])
    def test_old_response_only_credentials_are_hidden(self, detail, source, request_view, fake_gateway, fake_resource):
        secret = "legacy-response-only-ticket"
        body = {"echo": secret, "nested": [{"echo": secret}], "count": 1}
        headers = {}
        if source == "body":
            body["access_token"] = secret
        else:
            headers["Set-Cookie"] = f"bk_token={secret}; Path=/; HttpOnly"
        history = G(
            APIDebugHistory,
            gateway=fake_gateway,
            resource_name=fake_resource.name,
            request={"body": json.dumps({"echo": secret})},
            response={"data": {"body": json.dumps(body), "headers": headers}},
        )
        params = {"gateway_id": fake_gateway.id}
        if detail:
            params["id"] = history.id
        response = request_view(
            "GET",
            "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list",
            path_params=params,
            gateway=fake_gateway,
        )
        assert response.status_code == 200
        assert secret not in response.content.decode()
        item = response.json()["data"] if detail else response.json()["data"][0]
        assert json.loads(item["response"]["data"]["body"])["count"] == 1
        history.refresh_from_db()
        assert secret in history.request["body"]

    @pytest.mark.parametrize("detail", [False, True])
    def test_old_history_credentials_are_hidden(self, detail, request_view, fake_gateway, fake_resource):
        history = G(
            APIDebugHistory,
            resource_name=fake_resource.name,
            gateway=fake_gateway,
            request={
                "headers": {
                    "AUTHORIZATION": "Bearer old-personal-token",
                    "X-API-KEY": "old-api-key",
                    "X-Trace": "trace",
                }
            },
            response={
                "data": {
                    "curl": "curl -H 'Authorization: Bearer old-personal-token' http://example.com",
                    "body": "old-personal-token/old-api-key/issued-token",
                    "headers": {"Authorization": "Bearer issued-token", "Set-Cookie": "session=issued-cookie"},
                }
            },
        )
        params = {"gateway_id": fake_gateway.id}
        if detail:
            params["id"] = history.id
        response = request_view(
            "GET", "api_debug.histories.retrieve-destroy" if detail else "api_debug.histories.list", path_params=params
        )
        assert response.status_code == 200
        assert "old-personal-token" not in response.content.decode()
        assert "old-api-key" not in response.content.decode()
        assert "issued-token" not in response.content.decode()
        assert "issued-cookie" not in response.content.decode()
        item = response.json()["data"] if detail else response.json()["data"][0]
        assert item["request"]["headers"] == {"X-Trace": "trace"}
        history.refresh_from_db()
        assert history.request["headers"]["AUTHORIZATION"] == "Bearer old-personal-token"

    def test_list(self, request_view, fake_resource, fake_gateway):
        G(APIDebugHistory, resource_name="aa", gateway=fake_gateway, created_time=dummy_time.time)
        G(APIDebugHistory, resource_name="aaa", gateway=fake_gateway, created_time=dummy_time.time)
        G(
            APIDebugHistory,
            resource_name="bb",
            gateway=fake_gateway,
            created_time=dummy_time.time + datetime.timedelta(seconds=-300),
        )
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id},
            view_name="api_debug.histories.list",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert len(result["data"]) == 3
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id},
            view_name="api_debug.histories.list",
            data={
                "resource_name": "aa",
            },
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) == 2

        # 时间参数单测
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id},
            view_name="api_debug.histories.list",
            data={
                "time_start": dummy_time.timestamp,
                "time_end": dummy_time.timestamp + 10,
            },
        )
        result = resp.json()
        assert resp.status_code == 200
        assert len(result["data"]) == 2

    def test_retrieve(self, request_view, fake_gateway, fake_resource):
        fake_history = G(APIDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway)
        resp = request_view(
            method="GET",
            path_params={"gateway_id": fake_gateway.id, "id": fake_history.id},
            view_name="api_debug.histories.retrieve-destroy",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_history.id

    def test_destroy(self, request_view, fake_gateway, fake_resource):
        fake_history = G(APIDebugHistory, resource_name=fake_resource.name, gateway=fake_gateway)
        resp = request_view(
            method="DELETE",
            path_params={"gateway_id": fake_gateway.id, "id": fake_history.id},
            view_name="api_debug.histories.retrieve-destroy",
        )

        assert resp.status_code == 204
