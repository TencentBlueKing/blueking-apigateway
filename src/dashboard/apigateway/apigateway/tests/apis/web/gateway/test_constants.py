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

from apigateway.apis.web.gateway.constants import GATEWAY_NAME_PATTERN


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
def test_api_name_pattern(value, match):
    if match:
        assert GATEWAY_NAME_PATTERN.match(value)
    else:
        assert not GATEWAY_NAME_PATTERN.match(value)
