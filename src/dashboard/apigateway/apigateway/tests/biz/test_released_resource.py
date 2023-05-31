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
import json

import pytest
from ddf import G

from apigateway.biz.released_resource import ReleasedResourceData, get_released_resource_data
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestReleasedResource:
    @pytest.mark.parametrize(
        "config, expected",
        [
            (
                {},
                {
                    "verified_user_required": False,
                    "resource_perm_required": False,
                },
            ),
            (
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": False,
                    "resource_perm_required": False,
                },
                {
                    "verified_user_required": False,
                    "resource_perm_required": False,
                },
            ),
            (
                {
                    "skip_auth_verification": False,
                    "auth_verified_required": True,
                    "resource_perm_required": True,
                },
                {
                    "verified_user_required": True,
                    "resource_perm_required": True,
                },
            ),
            (
                {
                    "skip_auth_verification": True,
                    "auth_verified_required": True,
                    "resource_perm_required": True,
                },
                {
                    "verified_user_required": False,
                    "resource_perm_required": True,
                },
            ),
        ],
    )
    def test_init(self, config, expected):
        data = ReleasedResourceData(
            **{
                "id": 1,
                "method": "GET",
                "path": "/foo",
                "match_subpath": False,
                "contexts": {"resource_auth": {"config": json.dumps(config)}},
            }
        )
        assert data.verified_user_required == expected["verified_user_required"]
        assert data.resource_perm_required == expected["resource_perm_required"]


def test_get_released_resource_data(fake_gateway, fake_stage, fake_resource1, fake_released_resource):
    result = get_released_resource_data(fake_gateway, fake_stage, fake_resource1.id)
    assert result is not None

    # resource_version_id is None
    result = get_released_resource_data(G(Gateway), fake_stage, fake_resource1.id)
    assert result is None

    # released_resource is None
    result = get_released_resource_data(fake_gateway, fake_stage, 0)
    assert result is None
