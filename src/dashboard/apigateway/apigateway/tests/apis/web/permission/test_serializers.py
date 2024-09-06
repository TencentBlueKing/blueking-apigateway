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
from django.test import TestCase
from django_dynamic_fixture import G
from rest_framework.exceptions import ValidationError

from apigateway.apis.web.permission import serializers
from apigateway.apis.web.permission.views import AppPermissionQuerySetMixin
from apigateway.apps.permission import models
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.core.models import Gateway, Resource
from apigateway.tests.utils.testing import create_request, dummy_time

pytestmark = pytest.mark.django_db


class TestAppPermissionInputSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        mocker.patch("apigateway.apis.web.permission.serializers.BKAppCodeValidator.__call__")

    def test_to_internal_value(self, fake_resource):
        data = [
            {
                "bk_app_code": "apigw-test",
                "expire_days": 180,
                "resource_ids": [fake_resource.id],
            },
            {
                "bk_app_code": "apigw-test",
                "expire_days": None,
                "resource_ids": [fake_resource.id],
            },
            {
                "bk_app_code": "apigw-test",
                "expire_days": 180,
                "resource_ids": None,
            },
            {
                "bk_app_code": "apigw-test",
                "expire_days": 180,
                "resource_ids": None,
            },
            {
                "bk_app_code": "apigw-test",
                "expire_days": 180,
                "resource_ids": [],
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.AppPermissionInputSLZ(data=test, context={"gateway": fake_resource.gateway})

            if not test.get("will_error"):
                slz.is_valid(raise_exception=True)
                assert test == slz.validated_data
                continue

            with pytest.raises(ValidationError):
                slz.is_valid(raise_exception=True)


class TestAppPermissionOutputSLZ(TestCase):
    def test_to_representation(self):
        gateway = G(Gateway)
        resource = G(Resource, gateway=gateway, path="/echo/", method="GET")

        app_api_permission = G(
            models.AppGatewayPermission,
            gateway=gateway,
            bk_app_code="test",
            expires=None,
        )

        app_resource_permission = G(
            models.AppResourcePermission,
            gateway=gateway,
            resource_id=resource.id,
            bk_app_code="test",
            expires=dummy_time.time,
            grant_type="apply",
        )
        app_resource_permission.resource = resource

        api_permissions = AppGatewayPermission.objects.filter(gateway=gateway).order_by("-id")
        resource_permissions = AppResourcePermission.objects.filter(gateway=gateway).order_by("-id")
        permissions = AppPermissionQuerySetMixin().get_app_permissions(api_permissions, resource_permissions)
        slz = serializers.AppPermissionOutputSLZ(
            permissions,
            many=True,
            context={
                "resource_map": {resource.id: resource},
            },
        )
        assert slz.data == [
            {
                "bk_app_code": "test",
                "resource_id": 0,
                "resource_name": "",
                "resource_path": "",
                "resource_method": "",
                "expires": None,
                "grant_dimension": "api",
                "grant_type": "initialize",
                "renewable": False,
                "id": app_api_permission.id,
            },
            {
                "bk_app_code": "test",
                "resource_id": resource.id,
                "resource_name": resource.name,
                "resource_path": resource.path,
                "resource_method": resource.method,
                "expires": "2019-01-01 20:30:00",
                "grant_dimension": "resource",
                "grant_type": "apply",
                "renewable": True,
                "id": app_resource_permission.id,
            },
        ]


class TestAppPermissionIDsSLZ(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway, created_by="admin")
        cls.resource = G(Resource, gateway=cls.gateway)
        cls.request = create_request()
        cls.request.gateway = cls.gateway

    def test_to_internal_value(self):
        data = [
            {
                "ids": [1, 2],
                "expire_days": 0,
            },
            {
                "ids": [1, 2, 3],
                "expire_days": 0,
            },
        ]
        for test in data:
            slz = serializers.AppPermissionIDsSLZ(data=test)
            slz.is_valid()
            self.assertEqual(slz.validated_data, test)


class TestAppPermissionApplyApprovalInputSLZ(TestCase):
    def test_validate(self):
        data = [
            {
                "params": {
                    "ids": [1, 2, 3],
                    "status": "approved",
                    "comment": "ok",
                },
                "expected": {
                    "ids": [1, 2, 3],
                    "status": "approved",
                    "comment": "ok",
                },
            },
            {
                "params": {
                    "ids": [1, 2, 3],
                    "part_resource_ids": {
                        1: [1, 2],
                    },
                    "status": "approved",
                    "comment": "ok",
                },
                "expected": {
                    "ids": [1, 2, 3],
                    "part_resource_ids": {
                        "1": [1, 2],
                    },
                    "status": "approved",
                    "comment": "ok",
                },
            },
            {
                "params": {
                    "ids": [1, 2, 3],
                    "part_resource_ids": {},
                    "status": "approved",
                    "comment": "ok",
                },
                "expected": {
                    "ids": [1, 2, 3],
                    "part_resource_ids": {},
                    "status": "approved",
                    "comment": "ok",
                },
            },
            {
                "params": {
                    "ids": [1, 2, 3],
                    "part_resource_ids": {1: []},
                    "status": "approved",
                    "comment": "ok",
                },
                "will_error": True,
            },
        ]

        for test in data:
            slz = serializers.AppPermissionApplyApprovalInputSLZ(data=test["params"])
            slz.is_valid()
            if test.get("will_error"):
                self.assertTrue(slz.errors)
            else:
                self.assertEqual(slz.validated_data, test["expected"])
