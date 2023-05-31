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

from apigateway.common.constants import IP_OR_SEGMENT_PATTERN


class TestIPOrSegmentPattern:
    @pytest.mark.parametrize(
        "ip, expected",
        [
            ("1.0.0.1", True),
            ("1.0.0.1/8", True),
            ("1.0.0.289", False),
            ("1.0.0.1/35", False),
            ("1.1.1.1", True),
            ("1.1.2.0/24", True),
            ("::1", True),
            ("7f:0:0:0:0:1:5af8:7000", True),
            ("90a5:0:0:025e:0:0:5668:8af2", True),
            ("6a::5678:7e2e", True),
            ("::1:8:2222:0:0:7", True),
            ("::1:2:3:4", True),
            ("22:33:e:1FFF:1a:1f:1.0.0.1", True),
            ("2::/64", True),
            ("7f:0:0:0:0:1:5af8:7000/30", True),
            ("23456:5f:0:0:0:0:0:562a:1234", False),
            ("7f:0:0:0:0:1:5af8:7000/129", False),
        ],
    )
    def test(self, ip, expected):
        result = IP_OR_SEGMENT_PATTERN.match(ip)
        assert bool(result) == expected
