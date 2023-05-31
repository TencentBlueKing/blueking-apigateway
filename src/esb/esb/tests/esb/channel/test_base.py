# -*- coding: utf-8 -*-
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
import re

import pytest

from common import errors
from common.base_utils import FancyDict
from common.base_validators import ValidationError
from common.constants import COMPONENT_STATUSES
from common.errors import error_codes
from esb.channel.base import ApiChannel, BaseChannel, BaseChannelManager, RequestHandler
from esb.utils.base import preprocess_path_tmpl


class TestBaseChannelManager:
    def register_channel_groups(self, manager, path, method, rewrite_channels=None):
        manager.register_channel_groups(
            {}, [(path, {"comp_codename": "test", "method": method})], rewrite_channels or {}
        )

    @pytest.mark.parametrize(
        "method, path, expected",
        [
            ("GET", "/foo", 1),
            ("GET", "/foo/", 1),
            ("POST", "/foo/", 2),
            ("DELETE", "/foo", 3),
            ("GET", "/bar", None),
        ],
    )
    def test_get_channel_by_path(self, method, path, expected):
        manager = BaseChannelManager()
        manager.preset_channels = {
            "GET": {
                "/foo": 1,
            },
            "POST": {
                "/foo/": 2,
            },
            "DELETE": {
                "/foo/": 3,
            },
        }
        channel = manager.get_channel_by_path(path, method)
        assert channel == expected

    def test_update_rewrite_channels(self):
        manager = BaseChannelManager()
        manager.update_rewrite_channels({"/a/": "/b/"})
        assert manager.get_rewrite_path_by_path("/a/") == "/b/"

        manager.update_rewrite_channels({"/c/": "/d/"})
        assert manager.get_rewrite_path_by_path("/a/") == "/b/"
        assert manager.get_rewrite_path_by_path("/c/") == "/d/"

    @pytest.mark.parametrize(
        "method, path, expected",
        [
            ("GET", "/color/red", {"name": "red"}),
            ("GET", "/color/red/", None),
            ("GET", "/test/", None),
            ("GET", "/foo/bar/1/", {"bar": "bar", "id": "1"}),
        ],
    )
    def test_search_channel_by_repath(self, method, path, expected):
        manager = BaseChannelManager()
        manager.preset_channels_with_path_vars = {
            "GET": {
                "/color/{name}": {
                    "re_path": re.compile(r"^%s$" % preprocess_path_tmpl("/color/{name}")),
                },
                "/foo/{bar}/{id}/": {
                    "re_path": re.compile(r"^%s$" % preprocess_path_tmpl("/foo/{bar}/{id}/")),
                },
            }
        }

        _, path_vars = manager.search_channel_by_repath(path, method)
        if expected:
            assert path_vars.val_dict == expected
        else:
            assert path_vars is None

    def test_register_channel_groups(self):
        channels = [
            ("/color/red/", {"comp_codename": "generic.demo.red", "method": ""}),
            ("/color/green/", {"comp_codename": "generic.demo.green", "method": "DELETE"}),
            ("/color/{name}/", {"comp_codename": "generic.demo.name", "method": "POST"}),
        ]
        manager = BaseChannelManager()
        manager.register_channel_groups({}, channels, {"/foo": "/bar"})

        assert set(manager.preset_channels.keys()) == {"GET", "POST", "DELETE"}
        assert manager.preset_channels["GET"]["/color/red/"] is not None
        assert list(manager.preset_channels_with_path_vars.keys()) == ["POST"]
        assert manager.preset_channels_with_path_vars["POST"]["/color/{name}/"] is not None


class TestBaseChannel:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        self.request = mocker.MagicMock(META={"REMOTE_ADDR": "127.0.0.1"}, body="")
        self.comp_class = mocker.MagicMock()
        self.comp = self.comp_class.return_value
        self.path = "/"
        self.channel = BaseChannel(self.comp_class, self.path)

    def test_patch_request_common(self):
        self.channel.patch_request_common(self.request)

        for attr in [
            "system_name",
            "component_name",
            "component_alias_name",
            "client_ip",
            "request_id",
            "component_status",
            "channel_type",
            "use_test_env",
            "api_type",
            "headers",
            "channel_conf",
        ]:
            assert hasattr(self.request.g, attr), attr

    def test_invoke_exceptions(self, mocker):
        for raises, status, error_code in [
            (errors.CommonAPIError("test"), COMPONENT_STATUSES.ARGUMENT_ERROR, error_codes.COMMON_ERROR),
            (
                errors.RequestThirdPartyException(mocker.MagicMock(), "test", "test"),
                COMPONENT_STATUSES.EXCEPTION,
                error_codes.REQUEST_THIRD_PARTY_ERROR,
            ),
            (
                errors.RequestSSLException(mocker.MagicMock(), "test", "test"),
                COMPONENT_STATUSES.EXCEPTION,
                error_codes.REQUEST_SSL_ERROR,
            ),
            (
                errors.HostNotFoundException(),
                COMPONENT_STATUSES.EXCEPTION,
                error_codes.HOST_NOT_FOUND,
            ),
            (
                errors.RequestBlockedException(),
                COMPONENT_STATUSES.EXCEPTION,
                error_codes.REQUEST_BLOCKED,
            ),
            (
                Exception(),
                COMPONENT_STATUSES.EXCEPTION,
                error_codes.COMMON_ERROR,
            ),
        ]:
            self.comp.invoke.side_effect = raises

            response = self.channel.handle_request(self.request)
            result = json.loads(response.content)

            assert self.request.g.component_status == status
            assert result["code"] == error_code.code.code

    def test_invoke_comp(self):
        for result, status in [
            ({"result": False}, COMPONENT_STATUSES.FAILURE),
            ({"result": True}, COMPONENT_STATUSES.SUCCESS),
        ]:
            self.comp.invoke.return_value = result
            self.channel.handle_request(self.request)

            assert self.request.g.component_status == status

    def test_validate_error(self, mocker):
        request_validator = mocker.MagicMock()
        request_validator.validate.side_effect = ValidationError()

        channel = BaseChannel(self.comp_class, self.path, request_validators=[request_validator])
        response = channel.handle_request(self.request)

        result = json.loads(response.content)

        assert self.request.g.component_status == COMPONENT_STATUSES.ARGUMENT_ERROR
        assert result["code"] == error_codes.COMMON_ERROR.code.code

    @pytest.mark.parametrize(
        "header, expected",
        [
            ("X_BK_TOKEN", "X-Bk-Token"),
        ],
    )
    def test_capitalize_header(self, header, expected):
        assert expected == BaseChannel.capitalize_header(header)

    @pytest.mark.parametrize(
        "callback, expected",
        [
            (None, False),
            ("", False),
            ("test_<>", False),
            ("#test_01", False),
            ("test 01", False),
            ("test_01", True),
        ],
    )
    def test_is_valid_jsonp_callback(self, callback, expected):
        assert expected == self.channel._is_valid_jsonp_callback(callback)

    def test_patch_request_apigw(self, settings, mocker, fake_request):
        # API_GATEWAY_ADAPTER_ENABLED is False
        settings.API_GATEWAY_ADAPTER_ENABLED = False
        mock_is_from_gateway_with_jwt = mocker.patch("esb.channel.base.is_from_gateway_with_jwt")
        self.channel.patch_request_apigw(fake_request)
        mock_is_from_gateway_with_jwt.assert_not_called()

        # API_GATEWAY_ADAPTER_ENABLED is True
        settings.API_GATEWAY_ADAPTER_ENABLED = True

        # request is not from gateway
        mock_is_from_gateway_with_jwt = mocker.patch("esb.channel.base.is_from_gateway_with_jwt", return_value=False)
        self.channel.patch_request_apigw(fake_request)
        assert fake_request.apigw.enabled is False

        # request is from gateway, but enabled is True
        mock_is_from_gateway_with_jwt = mocker.patch("esb.channel.base.is_from_gateway_with_jwt", return_value=True)
        mocker.patch("esb.channel.base.JWTClient", return_value=mocker.MagicMock(enabled=True))
        self.channel.patch_request_apigw(fake_request)
        assert fake_request.apigw.enabled is True

        # request is from gateway, but enabled is False
        mock_is_from_gateway_with_jwt = mocker.patch("esb.channel.base.is_from_gateway_with_jwt", return_value=True)
        mocker.patch("esb.channel.base.JWTClient", return_value=mocker.MagicMock(enabled=False))
        self.channel.patch_request_apigw(fake_request)
        assert fake_request.apigw.enabled is False


class TestApiChannel:
    @pytest.mark.parametrize(
        "app_code, authorization, expected",
        [
            ("", {"bk_app_code": "app1"}, "app1"),
            ("", {"app_code": "app2"}, "app2"),
            ("exist-app", {"bk_app_code": "app1"}, "exist-app"),
            ("", {}, ""),
        ],
    )
    def test_before_handle_request(self, fake_request, mocker, app_code, authorization, expected):
        request = fake_request
        request.g = FancyDict(
            {
                "app_code": app_code,
                "authorization": authorization,
            }
        )

        channel = ApiChannel(mocker.MagicMock, "")
        channel.request = request

        channel.before_handle_request()
        assert request.g.app_code == expected


class TestRequestHandler:
    @pytest.mark.parametrize(
        "headers, params, expected",
        [
            ({}, {}, {}),
            (
                {"HTTP_X_BKAPI_AUTHORIZATION": json.dumps({"a": "b"})},
                {},
                {"a": "b"},
            ),
            (
                {},
                {"bk_app_code": "a", "bk_app_secret": "b", "c": "d"},
                {"bk_app_code": "a", "bk_app_secret": "b"},
            ),
            (
                {"HTTP_X_BKAPI_AUTHORIZATION": json.dumps({"a": "b"})},
                {"bk_app_code": "a", "bk_app_secret": "b", "c": "d"},
                {"a": "b"},
            ),
        ],
    )
    def test_get_request_authorization(self, request_factory, headers, params, expected):
        request = request_factory.get("", data=params, **headers)
        authorization = RequestHandler(request).get_request_authorization()
        assert authorization == expected

    @pytest.mark.parametrize(
        "headers, expected",
        [
            ({}, None),
            (
                {"HTTP_X_BKAPI_AUTHORIZATION": json.dumps({"a": "b"})},
                {"a": "b"},
            ),
        ],
    )
    def test_get_authorization_from_header(self, request_factory, headers, expected):
        request = request_factory.get("", **headers)
        authorization = RequestHandler(request)._get_authorization_from_header()
        assert authorization == expected

    def test_get_authorization_from_header_error(self, request_factory):
        request = request_factory.get("", HTTP_X_BKAPI_AUTHORIZATION="test")
        with pytest.raises(Exception):
            RequestHandler(request)._get_authorization_from_header()

    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "bk_app_code": "app1",
                    "bk_app_secret": "secret1",
                    "app_code": "app2",
                    "app_secret": "app3",
                    "bk_token": "token",
                    "bk_username": "admin1",
                    "username": "admin2",
                },
                {
                    "bk_app_code": "app1",
                    "bk_app_secret": "secret1",
                    "app_code": "app2",
                    "app_secret": "app3",
                    "bk_token": "token",
                    "bk_username": "admin1",
                    "username": "admin2",
                },
            ),
            (
                {"a": "b"},
                {},
            ),
            (
                {
                    "bk_app_code": "app",
                    "bk_app_secret": "secret",
                    "a": "b",
                },
                {
                    "bk_app_code": "app",
                    "bk_app_secret": "secret",
                },
            ),
        ],
    )
    def test_get_authorization_from_params(self, request_factory, params, expected):
        request = request_factory.get("", data=params)
        authorization = RequestHandler(request)._get_authorization_from_params()
        assert authorization == expected
