#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
import json
from unittest.mock import Mock

import pytest

from apigateway.apps.data_plane import constants
from apigateway.core.models import ResourceVersion


@pytest.mark.parametrize(
    "apisix_version, expected",
    [
        ("3.13", False),
        ("3.15.9", False),
        ("3.16", True),
        ("3.17", True),
        ("invalid", False),
        (None, False),
    ],
)
def test_is_apisix_version_supported_for_oauth2_resource(apisix_version, expected):
    assert constants.is_apisix_version_supported_for_oauth2_resource(apisix_version) is expected


def test_get_oauth2_resource_data_planes_compatibility_error():
    assert (
        constants.get_oauth2_resource_data_planes_compatibility_error(
            [
                ("apisix-3-13", "3.13"),
                ("apisix-3-16", "3.16"),
                ("broken", "invalid"),
            ]
        )
        == "OAuth2 public/personal resource clients require APISIX 3.16 or later; "
        "incompatible data planes: apisix-3-13 (3.13), broken (invalid)"
    )
    assert (
        constants.get_oauth2_resource_data_planes_compatibility_error(
            [
                ("apisix-3-16", "3.16"),
                ("apisix-3-17", "3.17"),
            ]
        )
        is None
    )


@pytest.mark.parametrize(
    "auth_config, expected",
    [
        ({}, False),
        ({"oauth2_public_client_enabled": False, "oauth2_personal_client_enabled": False}, False),
        ({"oauth2_public_client_enabled": True}, True),
        ({"oauth2_personal_client_enabled": True}, True),
    ],
)
def test_resource_version_uses_oauth2(auth_config, expected):
    resource_version = Mock(spec=ResourceVersion)
    resource_version.data = [
        {
            "contexts": {
                "resource_auth": {
                    "config": json.dumps(auth_config),
                }
            }
        }
    ]

    assert constants.resource_version_uses_oauth2(resource_version) is expected


def test_resource_version_without_resource_auth_context_does_not_use_oauth2():
    resource_version = Mock(spec=ResourceVersion)
    resource_version.data = [{"id": 1}]

    assert constants.resource_version_uses_oauth2(resource_version) is False
