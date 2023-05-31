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
import pytest

from apigateway.core import constants


class TestConstants:
    @pytest.mark.parametrize(
        "value, matched",
        [
            ("2001:db8:3333:4444:5555:6666:7777:8888", False),
            ("[2001:db8:3333:4444:5555:6666:7777:8888]", True),
            ("[2001:db8:3333:4444:5555:6666:7777:8888]:8000", True),
            ("[aaaa::7777:8888]:8000", True),
        ],
    )
    def test_domain_with_ipv6_pattern(self, value, matched):
        result = constants.DOMAIN_WITH_IPV6_PATTERN.match(value)
        assert bool(result) == matched

    @pytest.mark.parametrize(
        "value, matched",
        [
            ("http://2001:db8:3333:4444:5555:6666:7777:8888", False),
            ("http://[2001:db8:3333:4444:5555:6666:7777:8888]", True),
            ("https://[2001:db8:3333:4444:5555:6666:7777:8888]:8000", True),
            ("https://[aaaa::7777:8888]:8000/", True),
        ],
    )
    def test_domain_with_http_and_ipv6_pattern(self, value, matched):
        result = constants.DOMAIN_WITH_HTTP_AND_IPV6_PATTERN.match(value)
        assert bool(result) == matched

    @pytest.mark.parametrize(
        "value, matched",
        [
            ("http://0.0.0.1", True),
            ("http://0.0.0.1/", True),
            ("http://[2001:db8:3333:4444:5555:6666:7777:8888]", True),
            ("https://[2001:db8:3333:4444:5555:6666:7777:8888]/", True),
            ("https://2001:db8:3333:4444:5555:6666:7777:8888", False),
            ("http://0.0.0.1/a/", False),
        ],
    )
    def test_domain_pattern(self, value, matched):
        result = constants.DOMAIN_PATTERN.match(value)
        assert bool(result) == matched

    @pytest.mark.parametrize(
        "value, matched",
        [
            ("http://0.0.0.1", True),
            ("http://0.0.0.1/", True),
            ("http://[2001:db8:3333:4444:5555:6666:7777:8888]", True),
            ("https://[2001:db8:3333:4444:5555:6666:7777:8888]/", True),
            ("https://2001:db8:3333:4444:5555:6666:7777:8888", False),
            ("http://0.0.0.1/a/", False),
            ("http://{env.host}", True),
        ],
    )
    def test_resource_domain_pattern(self, value, matched):
        result = constants.RESOURCE_DOMAIN_PATTERN.match(value)
        assert bool(result) == matched

    @pytest.mark.parametrize(
        "value, match",
        [
            # ok
            ("abcd-123", True),
            # length < 3
            ("aa", False),
            # length > 32
            ("a" * 50, False),
            # include uppercase letter
            ("abA", False),
            # first letter is digit
            ("8ab", False),
            # include '_'
            ("ab_c", False),
        ],
    )
    def test_api_name_pattern(self, value, match):
        if match:
            assert constants.API_NAME_PATTERN.match(value)
        else:
            assert not constants.API_NAME_PATTERN.match(value)

    @pytest.mark.parametrize(
        "value, match",
        [
            # ok
            ("env.prod", True),
            ("envprod", False),
        ],
    )
    def test_stage_var_reference_pattern(self, value, match):
        if match:
            assert constants.STAGE_VAR_REFERENCE_PATTERN.match(value)
        else:
            assert not constants.STAGE_VAR_REFERENCE_PATTERN.match(value)

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("http://{env.domain}", ["domain"]),
            ("/{env.prefix}/{env.test}/", ["prefix", "test"]),
            ("http://{envxdomain}", []),
            ("/hello/", []),
        ],
    )
    def test_stage_var_pattern(self, value, expected):
        result = constants.STAGE_VAR_PATTERN.findall(value)
        assert result == expected

    @pytest.mark.parametrize(
        "value, match",
        [
            ("/hello", True),
            ("hello", True),
            ("/hello/?a=b", False),
            ("/hello/#fff", False),
        ],
    )
    def test_stage_var_for_path_pattern(self, value, match):
        result = constants.STAGE_VAR_FOR_PATH_PATTERN.match(value)
        if match:
            assert result
        else:
            assert not result

    @pytest.mark.parametrize(
        "value, match",
        [
            ("bking.com", True),
            ("bking.com:8000", True),
            ("1.0.0.1:12345", True),
            ("2001:db8:3333:4444:5555:6666:7777:8888", False),
            ("[2001:db8:3333:4444:5555:6666:7777:8888]", True),
            ("http://[2001:db8:3333:4444:5555:6666:7777:8888]", False),
            ("[2001:db8:3333:4444:5555:6666:7777:8888]:12345", True),
            ("bk-echo", True),
            ("http://bking.com", False),
            ("bking.com/", False),
        ],
    )
    def test_stage_var_for_domain_pattern(self, value, match):
        result = constants.HOST_WITHOUT_SCHEME_PATTERN.match(value)
        if match:
            assert result
        else:
            assert not result

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("/echo/{username}/", ["username"]),
            ("/hello/{env.region}/", ["env.region"]),
            ("/hello/{{uuid}}", ["{uuid"]),
        ],
    )
    def test_path_var_pattern(self, value, expected):
        result = constants.PATH_VAR_PATTERN.findall(value)
        assert result == expected

    @pytest.mark.parametrize(
        "value, expected",
        [
            ("env.username", "username"),
            ("envregion", None),
        ],
    )
    def test_stage_path_var_name_pattern(self, value, expected):
        result = constants.STAGE_PATH_VAR_NAME_PATTERN.match(value)
        if result:
            result = result.group(1)

        assert result == expected

    @pytest.mark.parametrize(
        "value, match",
        [
            ("1.0.0", True),
            ("1.0.0-beta.1", True),
            ("v1.0.0", False),
        ],
    )
    def test_semver_pattern(self, value, match):
        result = constants.SEMVER_PATTERN.match(value)
        if match:
            assert result
        else:
            assert not result
