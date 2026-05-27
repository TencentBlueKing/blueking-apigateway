#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

from apigateway.common.gateway_limits import get_max_resource_count


@pytest.mark.parametrize(
    "gateway_name, expected",
    [
        ("vip-gateway", 50),
        ("default-gateway", 20),
    ],
)
def test_get_max_resource_count(settings, gateway_name, expected):
    settings.API_GATEWAY_RESOURCE_LIMITS = {
        "max_resource_count_per_gateway": 20,
        "max_resource_count_per_gateway_whitelist": {
            "vip-gateway": 50,
        },
    }

    assert get_max_resource_count(gateway_name) == expected
