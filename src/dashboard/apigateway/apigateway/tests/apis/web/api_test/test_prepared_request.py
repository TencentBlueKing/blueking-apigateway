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

import pytest

from apigateway.apis.web.api_test.prepared_request import PreparedRequestHeaders, PreparedRequestURL, render_path
from apigateway.common.constants import HEADER_BKAPI_AUTHORIZATION


@pytest.mark.parametrize(
    "params, expected",
    [
        (
            {
                "path": "/echo/",
                "path_params": {},
            },
            "/echo/",
        ),
        (
            {
                "path": "/echo/{api_id}",
                "path_params": {"api_id": "123"},
            },
            "/echo/123",
        ),
        (
            {
                "path": "/echo/{api-id}",
                "path_params": {"api-id": "123"},
            },
            "/echo/123",
        ),
        (
            {
                "path": "/echo/{api-id}",
                "path_params": {},
            },
            "/echo/{api-id}",
        ),
        (
            {
                "path": "/echo/",
                "path_params": {"api_id": 123},
            },
            "/echo/",
        ),
    ],
)
def test_render_path(params, expected):
    result = render_path(**params)
    assert result == expected


class TestPreparedRequestHeaders:
    @pytest.mark.parametrize("scheme", ["Bearer", "bearer"])
    def test_bearer_token_replaces_application_and_other_token(self, scheme):
        request_headers = PreparedRequestHeaders()
        request_headers.prepare_headers(
            headers={
                "Authorization": f"{scheme} personal-token",
                "X-Bkapi-Authorization": '{"access_token": "other"}',
            },
            authorization={"bk_app_code": "app", "bk_app_secret": "secret"},
            authorization_from_cookies={"bk_token": "cookie-token"},
        )
        assert dict(request_headers.headers) == {"Authorization": f"{scheme} personal-token"}
        assert request_headers.uses_access_token

    @pytest.mark.parametrize("authorization", ["Basic abc", "Bearer "])
    def test_non_bearer_authorization_preserves_application(self, authorization):
        request_headers = PreparedRequestHeaders()
        request_headers.prepare_headers(
            headers={"Authorization": authorization},
            authorization={"bk_app_code": "app", "bk_app_secret": "secret"},
        )
        assert json.loads(request_headers.headers[HEADER_BKAPI_AUTHORIZATION])["bk_app_code"] == "app"
        assert not request_headers.uses_access_token

    def test_access_token_replaces_other_credentials(self):
        request_headers = PreparedRequestHeaders()
        headers = {"x-bkapi-authorization": json.dumps({"access_token": "access-token", "bk_app_code": "override"})}
        request_headers.prepare_headers(
            headers=headers,
            authorization={"bk_app_code": "app", "bk_app_secret": "secret", "bk_ticket": "ticket"},
            authorization_from_cookies={"bk_token": "cookie-token"},
        )
        assert json.loads(request_headers.headers[HEADER_BKAPI_AUTHORIZATION]) == {"access_token": "access-token"}
        assert json.loads(headers["x-bkapi-authorization"])["bk_app_code"] == "override"

    @pytest.mark.parametrize("name", ["Authorization", "authorization", "COOKIE", "Proxy-Authorization"])
    def test_curl_headers_hide_credentials(self, name):
        request_headers = PreparedRequestHeaders(headers={name: "Bearer personal-token", "X-Trace": "trace"})
        assert "personal-token" not in json.dumps(dict(request_headers.headers_without_sensitive))
        assert request_headers.headers_without_sensitive["X-Trace"] == "trace"
        assert request_headers.headers[name] == "Bearer personal-token"

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {},
                False,
            ),
            (
                {"authorization": {"bk_app_code": "foo"}},
                True,
            ),
            ({"headers": {"x-bkapi-authorization": '{"bk_app_code": "foo"}'}}, True),
        ],
    )
    def test_prepare_headers(self, params, expected):
        request_headers = PreparedRequestHeaders()
        request_headers.prepare_headers(**params)
        assert bool(request_headers.headers.get(HEADER_BKAPI_AUTHORIZATION)) is expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "authorization": {"bk_app_code": "foo", "bk_app_secret": "bar", "bk_token": ""},
                    "authorization_from_cookies": {"bk_token": "###"},
                    "headers": {"x-bkapi-authorization": '{"bk_token": "my-token"}'},
                },
                {"bk_app_code": "foo", "bk_app_secret": "bar", "bk_token": "my-token"},
            ),
            (
                {
                    "authorization": {"bk_app_code": "foo", "bk_app_secret": "bar", "bk_token": ""},
                    "authorization_from_cookies": {"bk_token": "token-in-cookies"},
                    "headers": {},
                },
                {"bk_app_code": "foo", "bk_app_secret": "bar", "bk_token": "token-in-cookies"},
            ),
        ],
    )
    def test_prepare_bkapi_authorization(self, params, expected):
        request_headers = PreparedRequestHeaders(headers=params.pop("headers"))
        result = request_headers._prepare_bkapi_authorization(**params)

        assert result == expected

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"headers": {}},
                {},
            ),
            (
                {"headers": {"x-bkapi-authorization": '{"foo": "bar"}'}},
                {"foo": "bar"},
            ),
        ],
    )
    def test_get_bkapi_authorization(self, params, expected):
        request_headers = PreparedRequestHeaders(**params)
        assert request_headers.get_bkapi_authorization() == expected

    def test_get_bkapi_authorization__error(self, mocker):
        request_headers = PreparedRequestHeaders(headers={"x-bkapi-authorization": "invalid-json"})
        with pytest.raises(ValueError):
            request_headers.get_bkapi_authorization()

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {"headers": {}},
                {},
            ),
            (
                {"headers": {"x-bkapi-authorization": '{"bk_app_code": "foo", "bk_app_secret": "bar"}'}},
                {HEADER_BKAPI_AUTHORIZATION: {"bk_app_code": "foo", "bk_app_secret": "***"}},
            ),
            (
                {
                    "headers": {
                        "x-bkapi-authorization": '{"bk_app_code": "foo", "bk_app_secret": "bar", "bk_token": ""}'
                    }
                },
                {HEADER_BKAPI_AUTHORIZATION: {"bk_app_code": "foo", "bk_app_secret": "***", "bk_token": ""}},
            ),
        ],
    )
    def test_headers_without_sensitive(self, params, expected):
        request_headers = PreparedRequestHeaders(**params)

        headers_without_sensitive = request_headers.headers_without_sensitive
        if headers_without_sensitive.get(HEADER_BKAPI_AUTHORIZATION):
            headers_without_sensitive[HEADER_BKAPI_AUTHORIZATION] = json.loads(
                headers_without_sensitive[HEADER_BKAPI_AUTHORIZATION]
            )

        assert headers_without_sensitive == expected


class TestPreparedRequestURL:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "resource_path": "/echo/",
                    "subpath": "",
                    "match_subpath": False,
                    "path_params": {},
                    "gateway_name": "foo",
                    "stage_name": "bar",
                },
                "http://example.com/foo/bar/echo/",
            ),
            (
                {
                    "resource_path": "/echo/{t}/",
                    "subpath": "",
                    "match_subpath": False,
                    "path_params": {"t": "test"},
                    "gateway_name": "foo",
                    "stage_name": "bar",
                },
                "http://example.com/foo/bar/echo/test/",
            ),
            (
                {
                    "resource_path": "/echo/{t}/",
                    "subpath": "/red",
                    "match_subpath": True,
                    "path_params": {"t": "test"},
                    "gateway_name": "foo",
                    "stage_name": "bar",
                },
                "http://example.com/foo/bar/echo/test/red",
            ),
        ],
    )
    def test_get_request_url(self, mocker, params, expected):
        mocker.patch(
            "apigateway.apis.web.api_test.prepared_request.get_resource_url_tmpl",
            return_value="http://example.com/{api_name}/{stage_name}/{resource_path}",
        )

        prepared_request_url = PreparedRequestURL(**params)
        assert prepared_request_url.request_url == expected
