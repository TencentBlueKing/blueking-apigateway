# -*- coding: utf-8 -*-
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
