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

from apigateway.apps.resource.swagger.helpers import AuthConfigConverter


class TestAuthConfigConverter:
    @pytest.mark.parametrize(
        "auth_config, expected",
        [
            (
                {
                    "auth_verified_required": True,
                    "app_verified_required": True,
                    "resource_perm_required": True,
                },
                {
                    "userVerifiedRequired": True,
                },
            ),
            (
                {
                    "auth_verified_required": False,
                    "app_verified_required": False,
                    "resource_perm_required": False,
                },
                {
                    "userVerifiedRequired": False,
                    "appVerifiedRequired": False,
                    "resourcePermissionRequired": False,
                },
            ),
        ],
    )
    def test_to_yaml(self, auth_config, expected):
        result = AuthConfigConverter.to_yaml(auth_config)
        assert result == expected

    @pytest.mark.parametrize(
        "auth_config, expected",
        [
            (
                {
                    "userVerifiedRequired": True,
                },
                {
                    "auth_verified_required": True,
                },
            ),
            (
                {
                    "userVerifiedRequired": False,
                    "appVerifiedRequired": False,
                    "resourcePermissionRequired": False,
                },
                {
                    "auth_verified_required": False,
                    "app_verified_required": False,
                    "resource_perm_required": False,
                },
            ),
        ],
    )
    def test_to_inner(self, auth_config, expected):
        result = AuthConfigConverter.to_inner(auth_config)
        assert result == expected
