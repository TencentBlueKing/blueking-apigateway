#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
    def test_get_bkapi_authorization_from_headers(self, params, expected):
        request_headers = PreparedRequestHeaders(**params)
        assert request_headers._get_bkapi_authorization_from_headers() == expected

    def test_get_bkapi_authorization_from_headers__error(self, mocker):
        request_headers = PreparedRequestHeaders(headers={"x-bkapi-authorization": "invalid-json"})
        with pytest.raises(ValueError):
            request_headers._get_bkapi_authorization_from_headers()

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
            "apigateway.apis.web.api_test.prepared_request.ResourceURLHandler.get_resource_url_tmpl",
            return_value="http://example.com/{api_name}/{stage_name}/{resource_path}",
        )

        prepared_request_url = PreparedRequestURL(**params)
        assert prepared_request_url.request_url == expected
