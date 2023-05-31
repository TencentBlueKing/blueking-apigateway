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

from apigateway.apps.docs.gateway.gateway import serializers


class TestGatewaySLZ:
    @pytest.mark.parametrize(
        "data, expected",
        [
            (
                {
                    "id": 1,
                    "api_type": 10,
                    "name": "t1",
                    "description": "d1",
                    "maintainers": ["admin"],
                    "user_auth_type": "open",
                },
                {
                    "id": 1,
                    "name": "t1",
                    "description": "d1",
                    "maintainers": ["admin"],
                    "name_prefix": "",
                    "user_auth_type": "open",
                    "user_auth_type_display": "open",
                    "api_url": "http://t1.example.com",
                },
            ),
            (
                {
                    "id": 1,
                    "api_type": 1,
                    "name": "t1",
                    "description": "d1",
                    "maintainers": ["admin"],
                    "user_auth_type": "open",
                },
                {
                    "id": 1,
                    "name": "t1",
                    "description": "d1",
                    "maintainers": ["admin"],
                    "name_prefix": "[官方]",
                    "user_auth_type": "open",
                    "user_auth_type_display": "open",
                    "api_url": "http://t1.example.com",
                },
            ),
            (
                {
                    "id": 1,
                    "api_type": 0,
                    "name": "t1",
                    "description": "d1",
                    "maintainers": ["admin"],
                    "user_auth_type": "open",
                },
                {
                    "id": 1,
                    "name": "t1",
                    "description": "d1",
                    "maintainers": ["admin"],
                    "name_prefix": "[官方]",
                    "user_auth_type": "open",
                    "user_auth_type_display": "open",
                    "api_url": "http://t1.example.com",
                },
            ),
        ],
    )
    def test_validate(
        self,
        settings,
        data,
        expected,
    ):
        settings.BK_API_URL_TMPL = "http://{api_name}.example.com"

        slz = serializers.GatewaySLZ(data)
        assert slz.data == expected
