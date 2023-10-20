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
from rest_framework.exceptions import ValidationError

from apigateway.apis.open.gateway import serializers
from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.constants import GatewayStatusEnum


class TestGatewayListV1InputSLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "user_auth_type": "default",
                    "name": "test",
                    "fuzzy": True,
                },
                {
                    "user_auth_type": "default",
                    "name": "test",
                    "fuzzy": True,
                },
            ),
            (
                {
                    "user_auth_type": "default",
                    "query": "test",
                    "fuzzy": True,
                },
                {
                    "user_auth_type": "default",
                    "query": "test",
                    "fuzzy": True,
                },
            ),
            (
                {
                    "user_auth_type": "default",
                },
                {
                    "user_auth_type": "default",
                },
            ),
            (
                {},
                {},
            ),
        ],
    )
    def test_validate(self, params, expected):
        slz = serializers.GatewayListV1InputSLZ(data=params)
        slz.is_valid(raise_exception=True)
        assert slz.validated_data == expected


class TestGatewayListV1OutputSLZ:
    def test_to_representation(self, fake_gateway):
        slz = serializers.GatewayListV1OutputSLZ(
            fake_gateway,
            context={
                "gateway_auth_configs": GatewayAuthContext().get_gateway_id_to_auth_config([fake_gateway.id]),
            },
        )
        assert slz.data
        assert isinstance(slz.data["api_type"], int)
        assert isinstance(slz.data["user_auth_type"], str)


class TestGatewayRetrieveV1OutputSLZ:
    def test_to_representation(self, fake_gateway):
        slz = serializers.GatewayRetrieveV1OutputSLZ(fake_gateway)
        assert slz.data
        assert "api_type" not in slz.data["api_type"]
        assert "user_auth_type" not in slz.data["user_auth_type"]


class TestGatewaySyncInputSLZ:
    @pytest.mark.parametrize(
        "data, expected, will_error",
        [
            (
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                    "api_type": 10,
                },
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                    "gateway_type": 10,
                    "status": GatewayStatusEnum.ACTIVE.value,
                    "maintainers": [],
                },
                False,
            ),
            (
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                },
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                    "status": GatewayStatusEnum.ACTIVE.value,
                    "maintainers": [],
                },
                False,
            ),
            (
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": False,
                    "status": GatewayStatusEnum.INACTIVE.value,
                    "maintainers": ["admin"],
                },
                {
                    "name": "test",
                    "description": "desc",
                    "maintainers": ["admin"],
                    "is_public": False,
                    "status": GatewayStatusEnum.INACTIVE.value,
                },
                False,
            ),
            (
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": False,
                    "status": GatewayStatusEnum.INACTIVE.value,
                    "maintainers": [],
                    "user_config": {
                        "from_bk_token": True,
                        "from_username": True,
                    },
                },
                {
                    "name": "test",
                    "description": "desc",
                    "maintainers": [],
                    "is_public": False,
                    "status": GatewayStatusEnum.INACTIVE.value,
                    "user_config": {
                        "from_bk_token": True,
                        "from_username": True,
                    },
                },
                False,
            ),
            (
                {
                    "name": "bk-test",
                    "description": "desc",
                    "is_public": True,
                    "api_type": 1,
                },
                {
                    "name": "bk-test",
                    "description": "desc",
                    "is_public": True,
                    "gateway_type": 1,
                    "status": GatewayStatusEnum.ACTIVE.value,
                    "maintainers": [],
                },
                False,
            ),
            (
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                    "api_type": 1,
                },
                None,
                True,
            ),
        ],
    )
    def test_validate(self, data, expected, will_error):
        slz = serializers.GatewaySyncInputSLZ(data=data)

        if not will_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)

    @pytest.mark.parametrize(
        "name, api_type, expected_error",
        [
            ("test", None, False),
            ("test", 10, False),
            ("bk-test", 1, False),
            ("bk-test", 0, False),
            ("foo-test", 1, False),
            ("test", 0, True),
            ("test", 1, True),
        ],
    )
    def test_validate_name(self, settings, name, api_type, expected_error):
        settings.OFFICIAL_GATEWAY_NAME_PREFIXES = ["bk-", "foo-"]
        slz = serializers.GatewaySyncInputSLZ()

        if not expected_error:
            slz._validate_name(name, api_type)
            return

        with pytest.raises(ValidationError):
            slz._validate_name(name, api_type)
