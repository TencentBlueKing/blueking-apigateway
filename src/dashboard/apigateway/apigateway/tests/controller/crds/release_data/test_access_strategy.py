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
import pytest
from ddf import G

from apigateway.apps.access_strategy.constants import AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import IPGroup
from apigateway.controller.crds.release_data.access_strategy import (
    AccessStrategyConvertorFactory,
    CorsASC,
    IpAccessControlASC,
    RateLimitASC,
    StatusCode200ASC,
    UserVerifiedUnrequiredAppsASC,
)


class TestIpAccessControlASC:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = IpAccessControlASC()

    @pytest.mark.parametrize(
        "ipContentList, expected",
        [
            (["127.0.0.1"], ["127.0.0.1"]),
            (["127.0.0.1\n192.168.1.1"], ["127.0.0.1", "192.168.1.1"]),
            (["127.0.0.1\n\n192.168.1.1"], ["127.0.0.1", "192.168.1.1"]),
            (["127.0.0.1\n # comment\n192.168.1.1"], ["127.0.0.1", "192.168.1.1"]),
            (["\n\n127.0.0.1\n192.168.1.1"], ["127.0.0.1", "192.168.1.1"]),
            (["\n # comment \n127.0.0.1\n192.168.1.1"], ["127.0.0.1", "192.168.1.1"]),
            (["127.0.0.1\n192.168.1.1\n 127.0.0.1\n192.168.1.1 "], ["127.0.0.1", "192.168.1.1"]),
            (["127.0.0.1/24\n\r192.168.1.1"], ["127.0.0.1/24", "192.168.1.1"]),
        ],
    )
    def test_parse_ip_content_list(self, ipContentList, expected):
        result = self.convertor._parse_ip_content_list(ipContentList)

        assert sorted(result) == sorted(expected)

    @pytest.mark.parametrize(
        "config, expected",
        [
            (
                {"type": "allow", "ip_group_list": [1]},
                {"whitelist": ["127.0.0.1"], "blacklist": []},
            ),
            (
                {"type": "deny", "ip_group_list": [1]},
                {"whitelist": [], "blacklist": ["127.0.0.1"]},
            ),
            (
                {"type": "allow", "ip_group_list": [2]},
                {"whitelist": ["127.0.0.1"], "blacklist": []},
            ),
            (
                {"type": "allow", "ip_group_list": [1, 2]},
                {"whitelist": ["127.0.0.1"], "blacklist": []},
            ),
        ],
    )
    def test_to_plugin_config(self, ip_access_control_access_strategy, config, expected):
        G(IPGroup, id=1, _ips="127.0.0.1")
        G(IPGroup, id=2, _ips="\n\r\n# comment\n127.0.0.1\n#test\n127.0.0.1")

        ip_access_control_access_strategy.config = config
        result = self.convertor._to_plugin_config(ip_access_control_access_strategy)
        assert result == expected


class TestCorsASC:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = CorsASC()

    @pytest.mark.parametrize(
        "config, expected",
        [
            (
                {
                    "allowed_origins": ["http://demo.example.com"],
                    "allowed_methods": ["GET", "POST", "options"],
                    "allowed_headers": ["X-Token", "x-requested-with"],
                    "exposed_headers": ["X-Token", "x-foo"],
                    "max_age": 0,
                    "allow_credentials": True,
                },
                {
                    "allow_origins": "http://demo.example.com",
                    "allow_methods": "GET,POST,OPTIONS",
                    "allow_headers": "X-Token,X-Requested-With",
                    "expose_headers": "X-Token,X-Foo",
                    "max_age": 0,
                    "allow_credential": True,
                },
            ),
            (
                {
                    "allowed_origins": ["http://demo.example.com", "http://*.example.com"],
                    "allowed_methods": ["GET"],
                    "allowed_headers": ["X-Token"],
                    "exposed_headers": ["X-Token"],
                    "max_age": 20,
                    "allow_credentials": False,
                },
                {
                    "allow_origins": "http://demo.example.com",
                    "allow_origins_by_regex": [r"^http://.*\.example\.com$"],
                    "allow_methods": "GET",
                    "allow_headers": "X-Token",
                    "expose_headers": "X-Token",
                    "max_age": 20,
                    "allow_credential": False,
                },
            ),
        ],
    )
    def test_to_plugin_config(self, cors_access_strategy, config, expected):
        cors_access_strategy.config = config
        result = self.convertor._to_plugin_config(cors_access_strategy)
        assert result == expected

    @pytest.mark.parametrize(
        "allowed_origins, expected_allow_origins, expected_allow_origins_by_regex",
        [
            (
                ["*"],
                "**",
                None,
            ),
            (
                ["http://demo.example.com", "*"],
                "**",
                None,
            ),
            (
                ["http://foo.example.com", "http://bar.example.com"],
                "http://foo.example.com,http://bar.example.com",
                [],
            ),
            (
                ["http://*.foo.com", "http://*.bar.com"],
                "null",
                [r"^http://.*\.foo\.com$", r"^http://.*\.bar\.com$"],
            ),
            (
                ["http://demo.example.com", "http://*.foo.com"],
                "http://demo.example.com",
                [r"^http://.*\.foo\.com$"],
            ),
            (
                ["http://*.demo-example.com"],
                "null",
                [r"^http://.*\.demo\-example\.com$"],
            ),
            (
                ["http://[2001:db8:3333:4444:5555:6666:7777:8888]:8000"],
                "http://[2001:db8:3333:4444:5555:6666:7777:8888]:8000",
                [],
            ),
            (
                ["http://[2001:db8:3333:4444:5555:6666:7777:8888]:*"],
                "null",
                [r"^http://\[2001:db8:3333:4444:5555:6666:7777:8888\]:.*$"],
            ),
        ],
    )
    def test_convert_allowed_origins(self, allowed_origins, expected_allow_origins, expected_allow_origins_by_regex):
        allow_origins, allow_origins_by_regex = self.convertor._convert_allowed_origins(allowed_origins)
        assert allow_origins == expected_allow_origins
        assert allow_origins_by_regex == expected_allow_origins_by_regex

    @pytest.mark.parametrize(
        "allowed_methods, expected",
        [
            (
                ["GET"],
                "GET",
            ),
            (
                ["GET", "POST"],
                "GET,POST",
            ),
            (
                ["get", "post"],
                "GET,POST",
            ),
        ],
    )
    def test_convert_allowed_methods(self, allowed_methods, expected):
        result = self.convertor._convert_allowed_methods(allowed_methods)
        assert result == expected

    @pytest.mark.parametrize(
        "allowed_headers, expected",
        [
            (
                ["*"],
                "**",
            ),
            (
                ["X-Token", "*"],
                "**",
            ),
            (
                ["x-token", "x-foo"],
                "X-Token,X-Foo",
            ),
        ],
    )
    def test_convert_allowed_headers(self, allowed_headers, expected):
        result = self.convertor._convert_allowed_headers(allowed_headers)
        assert result == expected

    @pytest.mark.parametrize(
        "exposed_headers, expected",
        [
            (
                ["*"],
                "**",
            ),
            (
                ["X-Token", "*"],
                "**",
            ),
            (
                ["X-Token", "x-foo"],
                "X-Token,X-Foo",
            ),
        ],
    )
    def test_convert_expose_headers(self, exposed_headers, expected):
        result = self.convertor._convert_expose_headers(exposed_headers)
        assert result == expected


class TestAccessStrategyConvertorFactory:
    def test_get_convertor(self):
        convertor = AccessStrategyConvertorFactory.get_convertor(AccessStrategyTypeEnum.ERROR_STATUS_CODE_200)
        assert isinstance(convertor, StatusCode200ASC)

        convertor = AccessStrategyConvertorFactory.get_convertor(AccessStrategyTypeEnum.USER_VERIFIED_UNREQUIRED_APPS)
        assert isinstance(convertor, UserVerifiedUnrequiredAppsASC)

        convertor = AccessStrategyConvertorFactory.get_convertor(AccessStrategyTypeEnum.CORS)
        assert isinstance(convertor, CorsASC)

        convertor = AccessStrategyConvertorFactory.get_convertor(AccessStrategyTypeEnum.RATE_LIMIT)
        assert isinstance(convertor, RateLimitASC)

        convertor = AccessStrategyConvertorFactory.get_convertor(AccessStrategyTypeEnum.IP_ACCESS_CONTROL)
        assert isinstance(convertor, IpAccessControlASC)
