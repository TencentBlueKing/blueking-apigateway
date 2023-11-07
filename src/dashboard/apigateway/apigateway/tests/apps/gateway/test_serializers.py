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
from unittest import mock

import arrow
import pytest
from django.test import TestCase
from django_dynamic_fixture import G
from rest_framework.serializers import DateTimeField

from apigateway.apps.gateway.serializers import (
    GatewayCreateSLZ,
    GatewayDetailSLZ,
    GatewayListSLZ,
    GatewayUpdateSLZ,
    GatewayUpdateStatusSLZ,
)
from apigateway.biz.gateway import GatewayHandler
from apigateway.core.models import JWT, Gateway, MicroGateway, Resource, Stage
from apigateway.tests.utils.testing import create_request
from apigateway.utils.crypto import calculate_fingerprint


class TestAPICreateSLZ:
    @pytest.fixture(autouse=True)
    def setUpTestData(self):
        self.request = create_request()

    @pytest.mark.parametrize(
        "check_reserved_gateway_name, data, expected, will_error",
        [
            # ok
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "developers": ["t1", "t2"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                    "bk_app_codes": ["app1", "app2"],
                },
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "developers": ["t1", "t2"],
                    "status": 1,
                    "is_public": True,
                    "hosting_type": 0,
                    "user_auth_type": "ieod",
                    "bk_app_codes": ["app1", "app2"],
                },
                False,
            ),
            # hosting_type
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "status": 1,
                    "is_public": True,
                    "hosting_type": 1,
                    "user_auth_type": "ieod",
                },
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "developers": [],
                    "status": 1,
                    "is_public": True,
                    "hosting_type": 1,
                    "user_auth_type": "ieod",
                },
                False,
            ),
            # name length < 3
            (
                False,
                {
                    "name": "ab",
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                },
                None,
                True,
            ),
            # name length > 32
            (
                False,
                {
                    "name": "a" * 50,
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                },
                None,
                True,
            ),
            # name contains invalid charactor
            (
                False,
                {
                    "name": "a_b_c",
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                },
                None,
                True,
            ),
            # name exists
            (
                False,
                {
                    "name": "create-test-exists",
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                },
                None,
                True,
            ),
            # status invalid
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 100,
                    "is_public": True,
                    "user_auth_type": "ieod",
                },
                None,
                True,
            ),
            # user_auth_type invalid
            (
                False,
                {
                    "name": "test",
                    "description": "test",
                    "maintainers": ["admin"],
                    "status": 0,
                    "is_public": True,
                    "user_auth_type": "ieod-test",
                },
                None,
                True,
            ),
            # name startswith bk-
            (
                True,
                {
                    "name": "bk-test",
                    "description": "test",
                    "maintainers": ["admin", "guest"],
                    "status": 1,
                    "is_public": True,
                    "user_auth_type": "ieod",
                },
                None,
                True,
            ),
        ],
    )
    def test(self, settings, check_reserved_gateway_name, data, expected, will_error):
        settings.DEFAULT_GATEWAY_HOSTING_TYPE = 0
        settings.DEFAULT_USER_AUTH_TYPE = "default"
        settings.CHECK_RESERVED_GATEWAY_NAME = check_reserved_gateway_name
        G(Gateway, name="create-test-exists")

        slz = GatewayCreateSLZ(data=data, context={"request": self.request})
        slz.is_valid()
        if will_error:
            assert slz.errors
            return

        assert slz.validated_data == expected


class TestAPIUpdateSLZ(TestCase):
    def test(self):
        data = [
            # ok
            {
                "maintainers": ["admin"],
                "developers": ["foo"],
                "description": "test",
                "is_public": True,
                "bk_app_codes": ["app1", "app2"],
                "will_error": False,
                "expected": {
                    "maintainers": ["admin"],
                    "developers": ["foo"],
                    "description": "test",
                    "is_public": True,
                    "bk_app_codes": ["app1", "app2"],
                },
            },
            # ok, is_public is str
            {
                "maintainers": ["admin"],
                "description": "test",
                "is_public": "True",
                "will_error": False,
                "expected": {
                    "maintainers": ["admin"],
                    "developers": [],
                    "description": "test",
                    "is_public": True,
                },
            },
            # ok, input parameters include status
            {
                "maintainers": ["admin"],
                "description": "test",
                "is_public": "True",
                "status": 1,
                "will_error": False,
                "expected": {
                    "maintainers": ["admin"],
                    "developers": [],
                    "description": "test",
                    "is_public": True,
                },
            },
        ]

        gateway = G(Gateway)

        for test in data:
            slz = GatewayUpdateSLZ(instance=gateway, data=test)
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
                continue
            self.assertEqual(slz.validated_data, test["expected"])


class TestAPIUpdateStatusSLZ(TestCase):
    def test(self):
        data = [
            # ok
            {
                "status": 0,
                "will_error": False,
                "expected": {
                    "status": 0,
                },
            },
            # ok, input parameters include is_public
            {
                "status": 0,
                "is_public": True,
                "will_error": False,
                "expected": {
                    "status": 0,
                },
            },
            {
                "status": 100,
                "will_error": True,
            },
        ]

        gateway = G(Gateway)

        for test in data:
            slz = GatewayUpdateStatusSLZ(instance=gateway, data=test)
            slz.is_valid()
            if test["will_error"]:
                self.assertTrue(slz.errors)
                continue
            self.assertEqual(slz.validated_data, test["expected"])


class TestAPIDetailSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixture(self, mocker):
        mocker.patch(
            "apigateway.biz.gateway.APIAuthConfig.config",
            new_callable=mock.PropertyMock(
                return_value={
                    "user_auth_type": "default",
                    "api_type": 10,
                    "unfiltered_sensitive_keys": [],
                    "allow_update_api_auth": False,
                    "user_conf": {
                        "user_type": "default",
                        "from_bk_token": True,
                    },
                }
            ),
        )

        self.api = G(Gateway, created_time=arrow.get("2019-01-01 12:30:00").datetime)
        self.jwt = JWT.objects.create_jwt(self.api)
        self.context, _ = GatewayHandler().save_auth_config(self.api.id, "default")

    def test_to_representation(self, mocker):
        mocker.patch(
            "apigateway.apps.gateway.serializers.get_gateway_feature_flags",
            return_value={"MICRO_GATEWAY_ENABLED": True},
        )
        data = {
            "api": self.api,
            "expected": {
                "id": self.api.id,
                "name": self.api.name,
                "description": self.api.description,
                "description_en": self.api.description_en,
                "maintainers": self.api.maintainers,
                "developers": self.api.developers,
                "status": self.api.status,
                "is_public": self.api.is_public,
                "hosting_type": self.api.hosting_type,
                "created_by": self.api.created_by,
                "created_time": "2019-01-01 20:30:00",
                "public_key": self.jwt.public_key,
                "user_auth_type": "default",
                "allow_update_api_auth": False,
                "domain": self.api.domain,
                "docs_url": self.api.docs_url,
                "public_key_fingerprint": calculate_fingerprint(self.jwt.public_key),
                "feature_flags": {"MICRO_GATEWAY_ENABLED": True},
                "is_official": False,
                "bk_app_codes": [],
            },
        }
        result = GatewayDetailSLZ.from_instance(self.api)
        assert result.data == data["expected"]


class TestAPIListSLZ(TestCase):
    def test(self):
        gateway_1 = G(
            Gateway,
            created_by="admin",
            _maintainers="admin",
            name="api-list-test-1",
            status=True,
            is_public=True,
            hosting_type=0,
        )
        gateway_2 = G(
            Gateway,
            created_by="admin",
            _maintainers="admin",
            name="api-list-test-2",
            status=False,
            is_public=False,
            hosting_type=1,
        )
        stage_prod = G(Stage, api=gateway_1, name="prod")
        stage_test = G(Stage, api=gateway_1, name="test")
        G(Resource, api=gateway_1)
        G(Resource, api=gateway_1)
        G(MicroGateway, api=gateway_1)

        expected = [
            {
                "id": gateway_1.id,
                "name": gateway_1.name,
                "description": gateway_1.description,
                "description_en": gateway_1.description_en,
                "created_by": gateway_1.created_by,
                "stages": [
                    {
                        "stage_id": stage_prod.id,
                        "stage_name": stage_prod.name,
                        "stage_release_status": False,
                    },
                    {
                        "stage_id": stage_test.id,
                        "stage_name": stage_test.name,
                        "stage_release_status": False,
                    },
                ],
                "resource_count": 2,
                "status": True,
                "is_public": True,
                "hosting_type": 1,
                "is_official": False,
                "created_time": DateTimeField().to_representation(gateway_1.created_time),
                "updated_time": DateTimeField().to_representation(gateway_1.updated_time),
            },
            {
                "id": gateway_2.id,
                "name": gateway_2.name,
                "description": gateway_2.description,
                "description_en": gateway_2.description_en,
                "created_by": gateway_2.created_by,
                "stages": [],
                "resource_count": 0,
                "status": False,
                "is_public": False,
                "hosting_type": 0,
                "is_official": False,
                "created_time": DateTimeField().to_representation(gateway_2.created_time),
                "updated_time": DateTimeField().to_representation(gateway_2.updated_time),
            },
        ]

        gateways = Gateway.objects.search_gateways("admin", "api-list-test")
        gateway_ids = [gateway_1.id, gateway_2.id]
        slz = GatewayListSLZ(
            gateways,
            many=True,
            context={
                "api_resource_count": Resource.objects.get_api_resource_count(gateway_ids),
                "api_stages": GatewayHandler().search_gateway_stages(gateway_ids),
                "api_auth_contexts": {},
                "micro_gateway_count": MicroGateway.objects.get_count_by_gateway(gateway_ids),
            },
        )
        self.assertEqual(slz.data, expected)
