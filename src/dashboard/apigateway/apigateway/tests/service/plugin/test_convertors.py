#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.service.plugin.convertor import (
    AIProxyConvertor,
    BkAccessTokenSourceConvertor,
    BkCorsConvertor,
    BkMockConvertor,
    BKUserRestrictionConvertor,
    DefaultPluginConvertor,
    HeaderWriteConvertor,
    IPRestrictionConvertor,
    PluginConvertorFactory,
    ProxyCacheConvertor,
    RedirectConvertor,
    ResponseRewriteConvertor,
)
from apigateway.utils.yaml import yaml_loads


class TestDefaultPluginConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = DefaultPluginConvertor()

    @pytest.mark.parametrize(
        "yaml_, expected",
        [
            (
                "a: 1",
                {"a": 1},
            ),
        ],
    )
    def test_convert(self, yaml_, expected):
        config = self.convertor.convert(yaml_loads(yaml_))
        assert config == expected


class TestIPRestrictionConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = IPRestrictionConvertor()

    @pytest.mark.parametrize(
        "item, expected",
        [
            (
                "1.1.1.1",
                ["1.1.1.1"],
            ),
            (
                "1.1.1.1\n2.2.2.2\n1.1.1.1",
                ["1.1.1.1", "2.2.2.2"],
            ),
            (
                ["1.1.1.1"],
                ["1.1.1.1"],
            ),
            (
                ["1.1.1.1", "2.2.2.2", "1.1.1.1"],
                ["1.1.1.1", "2.2.2.2"],
            ),
        ],
    )
    def test_parse_config_to_ips(self, item, expected):
        ips = self.convertor._parse_config_to_ips(item)
        assert sorted(ips) == sorted(expected)

    @pytest.mark.parametrize(
        "yaml_, expected",
        [
            (
                "whitelist: |-\n 1.1.1.1",
                {"whitelist": ["1.1.1.1"]},
            ),
            (
                "blacklist: |-\n 1.1.1.1",
                {"blacklist": ["1.1.1.1"]},
            ),
        ],
    )
    def test_convert(self, yaml_, expected):
        config = self.convertor.convert(yaml_loads(yaml_))
        assert config == expected

    @pytest.mark.parametrize(
        "yaml_, expected",
        [
            (
                "a: 1",
                {"a": 1},
            ),
        ],
    )
    def test_convert_error(self, yaml_, expected):
        with pytest.raises(ValueError):
            self.convertor.convert(yaml_loads(yaml_))


class TestHeaderWriteConvertor:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.convertor = HeaderWriteConvertor()

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"set": [{"key": "key1", "value": "value1"}], "remove": [{"key": "key2"}]},
                {"set": {"key1": "value1"}, "remove": ["key2"]},
            ),
        ],
    )
    def test_convert(self, data, expected):
        config = self.convertor.convert(data)
        assert config == expected


class TestBkCorsConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {},
                {"allow_origins": "null"},
            ),
            (
                {"foo": "bar"},
                {"foo": "bar", "allow_origins": "null"},
            ),
            (
                {"allow_origins": None},
                {"allow_origins": "null"},
            ),
            (
                {"allow_origins": ""},
                {"allow_origins": "null"},
            ),
            (
                {"allow_origins": "null"},
                {"allow_origins": "null"},
            ),
            (
                {"allow_origins": "foo"},
                {"allow_origins": "foo"},
            ),
            (
                {"allow_origins_by_regex": []},
                {"allow_origins": "null"},
            ),
            (
                {"allow_origins_by_regex": None},
                {"allow_origins": "null"},
            ),
            (
                {"allow_origins_by_regex": ["^http://.*\\.example\\.com$"]},
                {"allow_origins": "null", "allow_origins_by_regex": ["^http://.*\\.example\\.com$"]},
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = BkCorsConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestBkMockConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "response_status": 200,
                    "response_example": "mock1",
                    "response_headers": [],
                },
                {
                    "response_status": 200,
                    "response_example": "mock1",
                    "response_headers": {},
                },
            ),
            (
                {
                    "response_status": 200,
                    "response_example": "mock1",
                    "response_headers": [{"key": "mock1", "value": "mock1"}, {"key": "mock2", "value": "mock2"}],
                },
                {
                    "response_status": 200,
                    "response_example": "mock1",
                    "response_headers": {"mock1": "mock1", "mock2": "mock2"},
                },
            ),
            (
                {
                    "response_status": 200,
                    "response_example": "mock1",
                    "response_headers": [{"key": "mock1", "value": "mock1"}, {"key": "mock1", "value": "mock2"}],
                },
                {
                    "response_status": 200,
                    "response_example": "mock1",
                    "response_headers": {"mock1": "mock2"},
                },
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = BkMockConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestResponseRewriteConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "status_code": 200,
                    "body": '{"code":"ok","message":"new json body"}',
                    "headers": {
                        "add": [{"key": "name1", "value": "value1"}],
                        "set": [
                            {"key": "key1", "value": "value1"},
                            {"key": "key2", "value": "value2"},
                        ],
                        "remove": [{"key": "key2"}],
                    },
                },
                {
                    "status_code": 200,
                    "body": '{"code":"ok","message":"new json body"}',
                    "headers": {
                        "add": ["name1: value1"],
                        "set": {"key1": "value1", "key2": "value2"},
                        "remove": ["key2"],
                    },
                },
            ),
            (
                {
                    "status_code": 200,
                    "body": '{"code":"ok","message":"new json body"}',
                    "headers": {
                        "add": [],
                        "set": [],
                        "remove": [],
                    },
                },
                {
                    "status_code": 200,
                    "body": '{"code":"ok","message":"new json body"}',
                    "headers": {},
                },
            ),
            (
                {
                    "status_code": 200,
                    "body": "",
                    "headers": {
                        "add": [],
                    },
                },
                {
                    "status_code": 200,
                    "headers": {},
                },
            ),
            (
                {
                    "status_code": "200",
                    "body": "",
                    "headers": {
                        "add": [],
                    },
                },
                {
                    "status_code": 200,
                    "headers": {},
                },
            ),
            (
                {
                    "status_code": "",
                    "body": "",
                    "headers": {
                        "add": [],
                    },
                },
                {
                    "headers": {},
                },
            ),
            (
                {
                    "status_code": 0,
                    "body": "",
                    "headers": {
                        "add": [],
                    },
                },
                {
                    "headers": {},
                },
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = ResponseRewriteConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestRedirectConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"uri": "/test/default.html", "ret_code": 301},
                {"uri": "/test/default.html", "ret_code": 301},
            )
        ],
    )
    def test_convert(self, data, expected):
        convertor = RedirectConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestBkAccessTokenSourceConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"source": "bearer"},
                {"source": "bearer"},
            ),
            (
                {"source": "api_key"},
                {"source": "api_key"},
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = BkAccessTokenSourceConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestBKUserRestrictionConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "whitelist": [{"key": "admin"}],
                    "blacklist": [],
                },
                {"whitelist": ["admin"]},
            ),
            (
                {
                    "whitelist": [],
                    "blacklist": [{"key": "admin"}],
                },
                {"blacklist": ["admin"]},
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = BKUserRestrictionConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestProxyCacheConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "cache_method": [{"key": "GET"}],
                    "cache_ttl": 300,
                },
                {
                    "cache_method": ["GET"],
                    "cache_ttl": 300,
                    "cache_http_status": [200],
                    "no_cache": ["$arg_no_cache", "$http_no_cache"],
                },
            ),
            (
                {
                    "cache_method": [{"key": "GET"}, {"key": "HEAD"}],
                    "cache_ttl": 300,
                },
                {
                    "cache_method": ["GET", "HEAD"],
                    "cache_ttl": 300,
                    "cache_http_status": [200],
                    "no_cache": ["$arg_no_cache", "$http_no_cache"],
                },
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = ProxyCacheConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestAIProxyConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "provider": "openai",
                    "auth": {
                        "header": [{"key": "k1", "value": "v2"}],
                        "query": [],
                    },
                },
                {
                    "provider": "openai",
                    "auth": {
                        "header": {"k1": "v2"},
                    },
                },
            ),
            (
                {
                    "provider": "openai",
                    "auth": {
                        "header": [],
                        "query": [{"key": "k1", "value": "v2"}],
                    },
                },
                {
                    "provider": "openai",
                    "auth": {
                        "query": {"k1": "v2"},
                    },
                },
            ),
        ],
    )
    def test_convert(self, data, expected):
        convertor = AIProxyConvertor()
        result = convertor.convert(data)
        assert result == expected


class TestPluginConvertorFactory:
    def test_get_convertor(self):
        convertor = PluginConvertorFactory.get_convertor(PluginTypeCodeEnum.BK_IP_RESTRICTION)
        assert isinstance(convertor, IPRestrictionConvertor)

        convertor = PluginConvertorFactory.get_convertor(PluginTypeCodeEnum.BK_RATE_LIMIT)
        assert isinstance(convertor, DefaultPluginConvertor)
