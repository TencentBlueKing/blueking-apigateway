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
from apigateway.core.models import APIRelatedApp, Gateway

pytestmark = pytest.mark.django_db


class TestAPIQueryV1SLZ:
    @pytest.mark.parametrize(
        "params, expected",
        [
            (
                {
                    "user_auth_type": "ieod",
                    "name": "test",
                    "fuzzy": True,
                },
                {
                    "user_auth_type": "ieod",
                    "name": "test",
                    "fuzzy": True,
                },
            ),
            (
                {
                    "user_auth_type": "ieod",
                    "query": "test",
                    "fuzzy": True,
                },
                {
                    "user_auth_type": "ieod",
                    "query": "test",
                    "fuzzy": True,
                },
            ),
            (
                {
                    "user_auth_type": "ieod",
                },
                {
                    "user_auth_type": "ieod",
                },
            ),
            (
                {},
                {},
            ),
        ],
    )
    def test_validate(self, params, expected):
        slz = serializers.GatewayQueryV1SLZ(data=params)
        slz.is_valid()
        assert slz.validated_data == expected


class TestGatewaySyncSLZ:
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
                    "api_type": 10,
                    "status": GatewayStatusEnum.ACTIVE.value,
                    "user_auth_type": "default",
                    "hosting_type": 1,
                    "maintainers": [],
                },
                False,
            ),
            (
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                    "hosting_type": 0,
                },
                {
                    "name": "test",
                    "description": "desc",
                    "is_public": True,
                    "status": GatewayStatusEnum.ACTIVE.value,
                    "user_auth_type": "default",
                    "hosting_type": 0,
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
                    "user_auth_type": "default",
                    "hosting_type": 1,
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
                    "user_auth_type": "default",
                    "user_config": {
                        "from_bk_token": True,
                        "from_username": True,
                    },
                    "hosting_type": 1,
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
                    "api_type": 1,
                    "status": GatewayStatusEnum.ACTIVE.value,
                    "user_auth_type": "default",
                    "hosting_type": 1,
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
    def test_validate(self, settings, data, expected, will_error):
        settings.DEFAULT_GATEWAY_HOSTING_TYPE = 1
        settings.DEFAULT_USER_AUTH_TYPE = "default"
        slz = serializers.GatewaySyncSLZ(data=data)

        if not will_error:
            slz.is_valid(raise_exception=True)
            assert slz.validated_data == expected
            return

        with pytest.raises(ValidationError):
            slz.is_valid(raise_exception=True)

    def test_create(self, settings, unique_gateway_name):
        settings.USE_BK_IAM_PERMISSION = False
        settings.SPECIAL_API_AUTH_CONFIGS = {
            unique_gateway_name: {
                "unfiltered_sensitive_keys": ["bk_token"],
            }
        }

        bk_app_code = "test"

        slz = serializers.GatewaySyncSLZ(
            data={
                "name": unique_gateway_name,
                "description": "desc",
                "is_public": True,
            },
            context={
                "bk_app_code": bk_app_code,
            },
        )
        slz.is_valid(raise_exception=True)
        slz.save(created_by="", updated_by="")

        assert Gateway.objects.filter(name=unique_gateway_name).exists()
        assert APIRelatedApp.objects.filter(api=slz.instance, bk_app_code=bk_app_code).exists()
        api_auth = GatewayAuthContext().get_config(slz.instance.id)
        assert api_auth["unfiltered_sensitive_keys"] == ["bk_token"]
        assert api_auth["api_type"] == 10

        api_name = f"bk-{unique_gateway_name}"
        slz = serializers.GatewaySyncSLZ(
            data={
                "name": api_name,
                "description": "desc",
                "is_public": True,
                "api_type": 1,
            },
            context={
                "bk_app_code": bk_app_code,
            },
        )
        slz.is_valid(raise_exception=True)
        slz.save(created_by="", updated_by="")
        api_auth = GatewayAuthContext().get_config(slz.instance.id)
        api_auth["api_type"] == 1

    def test_update(self, settings, fake_gateway, unique_gateway_name):
        settings.SPECIAL_API_AUTH_CONFIGS = {
            fake_gateway.name: {
                "unfiltered_sensitive_keys": ["bk_red"],
            }
        }

        fake_gateway.maintainers = ["admin"]
        slz = serializers.GatewaySyncSLZ(
            instance=fake_gateway,
            data={
                "name": unique_gateway_name,
                "description": "desc",
                "is_public": False,
                "maintainers": ["admin2"],
            },
        )
        slz.is_valid()
        slz.save(created_by="", updated_by="")

        gateway = Gateway.objects.get(id=fake_gateway.id)
        assert gateway.name != unique_gateway_name
        assert gateway.description == "desc"
        assert gateway.is_public is False
        assert gateway.maintainers == ["admin", "admin2"]
        api_auth = GatewayAuthContext().get_config(gateway.id)
        assert api_auth["unfiltered_sensitive_keys"] == ["bk_red"]
        assert api_auth["api_type"] == 10

        slz = serializers.GatewaySyncSLZ(
            instance=fake_gateway,
            data={
                "name": f"bk-{unique_gateway_name}",
                "description": "desc",
                "is_public": True,
                "api_type": 1,
            },
        )
        slz.is_valid(raise_exception=True)
        slz.save(created_by="", updated_by="")
        api_auth = GatewayAuthContext().get_config(gateway.id)
        assert api_auth["api_type"] == 1

    @pytest.mark.parametrize(
        "api_name, special_api_auth_configs, expected",
        [
            ("my-color", {}, None),
            (
                "my-color",
                {
                    "my-color": {
                        "unfiltered_sensitive_keys": ["bk_token", "my_color"],
                    }
                },
                ["bk_token", "my_color"],
            ),
            (
                "not-exist",
                {
                    "my-color": {
                        "unfiltered_sensitive_keys": ["bk_token", "my_color"],
                    }
                },
                None,
            ),
        ],
    )
    def test_get_api_unfiltered_sensitive_keys(self, settings, api_name, special_api_auth_configs, expected):
        settings.SPECIAL_API_AUTH_CONFIGS = special_api_auth_configs
        slz = serializers.GatewaySyncSLZ(data={})

        result = slz._get_api_unfiltered_sensitive_keys(api_name)
        assert result == expected

    @pytest.mark.parametrize(
        "name, api_type, expected_error",
        [
            ("test", None, False),
            ("test", 10, False),
            ("bk-test", 1, False),
            ("bk-test", 0, False),
            ("test", 0, True),
            ("test", 1, True),
        ],
    )
    def test_validate_api_type(self, name, api_type, expected_error):
        slz = serializers.GatewaySyncSLZ()

        if not expected_error:
            slz._validate_api_type(name, api_type)
            return

        with pytest.raises(ValidationError):
            slz._validate_api_type(name, api_type)
