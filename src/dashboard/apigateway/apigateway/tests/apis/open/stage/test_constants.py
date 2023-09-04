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

from apigateway.apis.open.stage import constants


class TestConstants:
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
