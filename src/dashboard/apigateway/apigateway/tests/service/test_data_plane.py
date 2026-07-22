#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/MIT
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
from rest_framework.exceptions import ValidationError

from apigateway.apps.data_plane.constants import is_apisix_version_supported_for_ai_gateway
from apigateway.apps.data_plane.models import DataPlane
from apigateway.core.constants import GatewayKindEnum
from apigateway.core.models import Gateway
from apigateway.service.data_plane import validate_gateway_data_plane_compatibility


@pytest.mark.parametrize(
    ("apisix_version", "expected"),
    [
        ("3.13", False),
        ("3.16", True),
        ("3.17", True),
        ("invalid", False),
    ],
)
def test_is_apisix_version_supported_for_ai_gateway(apisix_version, expected):
    assert is_apisix_version_supported_for_ai_gateway(apisix_version) is expected


@pytest.mark.django_db
def test_validate_gateway_data_plane_compatibility_rejects_older_version():
    gateway = G(Gateway, kind=GatewayKindEnum.AI.value)
    data_plane = G(DataPlane, name="apisix-3-13", apisix_version="3.13")

    with pytest.raises(ValidationError) as exc_info:
        validate_gateway_data_plane_compatibility(gateway, [data_plane])

    assert str(exc_info.value.detail["data_planes"]) == (
        "AI Gateway requires APISIX 3.16 or later; incompatible data planes: apisix-3-13 (3.13)"
    )


@pytest.mark.django_db
def test_validate_gateway_data_plane_compatibility_keeps_standard_gateway_unchanged():
    gateway = G(Gateway, kind=GatewayKindEnum.NORMAL.value)
    data_plane = G(DataPlane, name="apisix-3-13", apisix_version="3.13")

    validate_gateway_data_plane_compatibility(gateway, [data_plane])
