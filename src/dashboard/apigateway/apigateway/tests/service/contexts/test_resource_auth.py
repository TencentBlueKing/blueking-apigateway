# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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
import pytest

from apigateway.service.contexts import with_resource_auth_derived_fields


@pytest.mark.parametrize(
    "config, expected_auth_type, expected_delegated",
    [
        ({"auth_verified_required": True, "app_verified_required": True}, "user", True),
        ({"auth_verified_required": True, "app_verified_required": False}, "user", False),
        ({"auth_verified_required": False, "app_verified_required": True}, "app", False),
        ({"auth_verified_required": False, "app_verified_required": False}, "none", False),
    ],
)
def test_with_resource_auth_derived_fields(config, expected_auth_type, expected_delegated):
    config = {**config, "resource_perm_required": False, "oauth2_public_client_enabled": False}

    result = with_resource_auth_derived_fields(config)

    assert result == {
        **config,
        "auth_type": expected_auth_type,
        "oauth2_app_delegated_enabled": expected_delegated,
    }
    assert "auth_type" not in config
