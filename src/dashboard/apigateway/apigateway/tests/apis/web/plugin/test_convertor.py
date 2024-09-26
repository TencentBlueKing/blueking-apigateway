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
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.plugin.convertor import (
    FaultInjectionYamlConvertor,
    IPRestrictionYamlConvertor,
    PluginConfigYamlConvertor,
    RateLimitYamlConvertor,
    RequestValidationYamlConvertor,
)
from apigateway.utils.yaml import yaml_dumps, yaml_loads


class TestRateLimitYamlConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "rates": {
                        "default": {"period": 1, "tokens": 10},
                        "specials": [{"period": 1, "tokens": 20, "bk_app_code": "test"}],
                    }
                },
                {"rates": {"__default": [{"period": 1, "tokens": 10}], "test": [{"period": 1, "tokens": 20}]}},
            ),
            (
                {
                    "rates": {
                        "default": {"period": 1, "tokens": 10},
                    }
                },
                {
                    "rates": {
                        "__default": [{"period": 1, "tokens": 10}],
                    }
                },
            ),
        ],
    )
    def test_to_internal_value(self, data, expected):
        convertor = RateLimitYamlConvertor()
        result = convertor.to_internal_value(yaml_dumps(data))
        assert yaml_loads(result) == expected

    @pytest.mark.parametrize(
        "data",
        [
            {
                "rates": {
                    "default": {"period": 1, "tokens": 10},
                    "specials": [
                        {"period": 1, "tokens": 20, "bk_app_code": "test"},
                        {"period": 1, "tokens": 20, "bk_app_code": "test"},
                    ],
                }
            },
        ],
    )
    def test_to_internal_value__error(self, data):
        convertor = RateLimitYamlConvertor()
        with pytest.raises(ValidationError):
            convertor.to_internal_value(yaml_dumps(data))

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {"rates": {"__default": [{"period": 1, "tokens": 10}], "test": [{"period": 1, "tokens": 20}]}},
                {
                    "rates": {
                        "default": {"period": 1, "tokens": 10},
                        "specials": [{"period": 1, "tokens": 20, "bk_app_code": "test"}],
                    }
                },
            ),
            (
                {
                    "rates": {
                        "__default": [{"period": 1, "tokens": 10}],
                    }
                },
                {
                    "rates": {
                        "default": {"period": 1, "tokens": 10},
                        "specials": [],
                    }
                },
            ),
        ],
    )
    def test_to_representation(self, data, expected):
        convertor = RateLimitYamlConvertor()
        result = convertor.to_representation(yaml_dumps(data))
        assert yaml_loads(result) == expected


class TestIPRestrictionYamlConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                "",
                "",
            ),
            (
                "whitelist: |- \n1.1.1.1",
                "whitelist: |- \n1.1.1.1",
            ),
            (
                "blacklist: |- \n1.1.1.1",
                "blacklist: |- \n1.1.1.1",
            ),
            (
                "whitelist:\n - 1.1.1.1",
                "whitelist: |-\n 1.1.1.1",
            ),
            (
                "blacklist:\n - 1.1.1.1",
                "blacklist: |-\n 1.1.1.1",
            ),
        ],
    )
    def test_to_representation(self, data, expected):
        convertor = IPRestrictionYamlConvertor()
        result = convertor.to_representation(data)
        assert result == expected


class TestRequestValidationYamlConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                """header_schema: '{"aa": "bb"}'
body_schema: '{"aa": "bb"}'
rejected_code: 400
rejected_msg: foo""",
                '{"header_schema": {"aa": "bb"}, "body_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": '
                '"foo"}',
            ),
            (
                """header_schema: '{"aa":"bb"}'
body_schema: ''
rejected_code: 400
rejected_msg: foo""",
                '{"header_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": "foo"}',
            ),
            (
                """header_schema: ''
body_schema: '{"aa":"bb"}'
rejected_code: 400
rejected_msg: foo""",
                '{"body_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": "foo"}',
            ),
        ],
    )
    def test_to_internal_value(self, data, expected):
        convertor = RequestValidationYamlConvertor()
        result = convertor.to_internal_value(data)
        assert result == expected

    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                '{"header_schema": {"aa": "bb"}, "body_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": '
                '"foo"}',
                """header_schema: '{"aa": "bb"}'
body_schema: '{"aa": "bb"}'
rejected_code: 400
rejected_msg: foo
""",
            ),
            (
                '{"header_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": "foo"}',
                """header_schema: '{"aa": "bb"}'
body_schema: ''
rejected_code: 400
rejected_msg: foo
""",
            ),
            (
                '{"body_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": "foo"}',
                """header_schema: ''
body_schema: '{"aa": "bb"}'
rejected_code: 400
rejected_msg: foo
""",
            ),
        ],
    )
    def test_to_representation(self, data, expected):
        convertor = RequestValidationYamlConvertor()
        result = convertor.to_representation(data)
        assert result == expected


class TestFaultInjectionYamlConvertor:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                # 全部都有数据的情况
                """{'abort': {'body': 'aaa', 'vars': ['[ "arg_name","==","jack" ]'], 'http_status': 200, 'percentage': 100}, 'delay': {'duration': '5', 'vars': ['[ "arg_name","==","jack" ]'], 'percentage': 100}}""",
                """abort:
  body: aaa
  http_status: 200
  percentage: 100
  vars:
  - - - arg_name
      - ==
      - jack
delay:
  duration: 5.0
  percentage: 100
  vars:
  - - - arg_name
      - ==
      - jack
""",
            ),
            (
                # delay 没有数据的时候，会不会直接没有这个的配置
                """{'abort': {'body': 'aaa', 'vars': ['[ "arg_name","==","jack" ]'], 'http_status': 200, 'percentage': 100}, 'delay': {'duration': '', 'vars': []}}""",
                """abort:
  body: aaa
  http_status: 200
  percentage: 100
  vars:
  - - - arg_name
      - ==
      - jack
""",
            ),
            (
                # abort 没有数据的时候
                """{'abort': {'body': '', 'vars': []}, 'delay': {'duration': '5', 'vars': ['[ "arg_name","==","jack" ]'], 'percentage': 100}}""",
                """delay:
  duration: 5.0
  percentage: 100
  vars:
  - - - arg_name
      - ==
      - jack
""",
            ),
        ],
    )
    def test_to_internal_value(self, data, expected):
        convertor = FaultInjectionYamlConvertor()
        result = convertor.to_internal_value(data)
        assert result == expected


#     @pytest.mark.parametrize(
#         "data, expected",
#         [
#             (
#                 '{"header_schema": {"aa": "bb"}, "body_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": '
#                 '"foo"}',
#                 """header_schema: '{"aa": "bb"}'
# body_schema: '{"aa": "bb"}'
# rejected_code: 400
# rejected_msg: foo
# """,
#             ),
#             (
#                 '{"header_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": "foo"}',
#                 """header_schema: '{"aa": "bb"}'
# body_schema: ''
# rejected_code: 400
# rejected_msg: foo
# """,
#             ),
#             (
#                 '{"body_schema": {"aa": "bb"}, "rejected_code": 400, "rejected_msg": "foo"}',
#                 """header_schema: ''
# body_schema: '{"aa": "bb"}'
# rejected_code: 400
# rejected_msg: foo
# """,
#             ),
#         ],
#     )
#     def test_to_representation(self, data, expected):
#         convertor = RequestValidationYamlConvertor()
#         result = convertor.to_representation(data)
#         assert result == expected


class TestPluginConfigYamlConvertor:
    @pytest.mark.parametrize(
        "type_code, data, expected",
        [
            (
                "bk-test",
                {"foo": "bar", "colors": ["green"]},
                {"foo": "bar", "colors": ["green"]},
            ),
            (
                "bk-rate-limit",
                {
                    "rates": {
                        "default": {"period": 1, "tokens": 10},
                        "specials": [],
                    }
                },
                {
                    "rates": {
                        "__default": [{"period": 1, "tokens": 10}],
                    }
                },
            ),
        ],
    )
    def test_to_internal_value(self, type_code, data, expected):
        convertor = PluginConfigYamlConvertor(type_code)
        result = convertor.to_internal_value(yaml_dumps(data))
        assert yaml_loads(result) == expected

    @pytest.mark.parametrize(
        "type_code, data, expected",
        [
            (
                "bk-test",
                {"foo": "bar", "colors": ["green"]},
                {"foo": "bar", "colors": ["green"]},
            ),
            (
                "bk-rate-limit",
                {
                    "rates": {
                        "__default": [{"period": 1, "tokens": 10}],
                    }
                },
                {
                    "rates": {
                        "default": {"period": 1, "tokens": 10},
                        "specials": [],
                    }
                },
            ),
        ],
    )
    def test_to_representation(self, type_code, data, expected):
        convertor = PluginConfigYamlConvertor(type_code)
        result = convertor.to_representation(yaml_dumps(data))
        assert yaml_loads(result) == expected
