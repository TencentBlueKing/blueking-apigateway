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
import shlex

import pytest
import requests
import responses
from ddf import G

from apigateway.apps.api_debug.models import APIDebugHistory
from apigateway.service.utils import get_resource_url
from apigateway.tests.utils.testing import dummy_time


class TestAPITestAPIView:
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
            "x-token": "test",
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
    def test_old_history_credentials_are_hidden(self, detail, request_view, fake_gateway, fake_resource):
        history = G(
            APIDebugHistory,
            resource_name=fake_resource.name,
            gateway=fake_gateway,
            request={"headers": {"AUTHORIZATION": "Bearer old-personal-token", "X-Trace": "trace"}},
            response={
                "data": {
                    "curl": "curl -H 'Authorization: Bearer old-personal-token' http://example.com",
                    "body": "old-personal-token",
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
