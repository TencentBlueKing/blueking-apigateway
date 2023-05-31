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
import json
from unittest import mock

import pytest
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.permission import models, views
from apigateway.apps.permission.helpers import AppPermissionHelper
from apigateway.core.models import Resource
from apigateway.tests.utils.testing import APIRequestFactory, create_gateway, dummy_time, get_response_json
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestAppPermissionViewSet:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, mocker):
        mocker.patch("apigateway.apps.permission.serializers.BKAppCodeValidator.__call__")

    def test_list(self, fake_resource, request_view):
        fake_gateway = fake_resource.api

        G(
            models.AppAPIPermission,
            api=fake_gateway,
            bk_app_code="test",
        )

        G(
            models.AppResourcePermission,
            api=fake_gateway,
            bk_app_code="test",
            resource_id=fake_resource.id,
            grant_type="apply",
        )
        G(
            models.AppResourcePermission,
            api=fake_gateway,
            bk_app_code="test-2",
            resource_id=fake_resource.id,
            grant_type="apply",
        )

        data = [
            {
                "params": {
                    "dimension": "api",
                    "bk_app_code": "test",
                    "grant_type": "initialize",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "dimension": "resource",
                    "bk_app_code": "",
                    "grant_type": "apply",
                },
                "expected": {
                    "count": 2,
                },
            },
        ]

        for test in data:
            response = request_view(
                "GET",
                "permissions.app-permissions",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data=test["params"],
            )

            result = response.json()
            assert result["code"] == 0, result
            assert result["data"]["count"] == test["expected"]["count"]

    def test_create(self, mocker, request_view, fake_resource):
        mocker.patch("apigateway.apps.permission.models.generate_expire_time", return_value=dummy_time.time)
        fake_gateway = fake_resource.api

        data = [
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": 180,
                    "resource_ids": [fake_resource.id],
                    "dimension": "resource",
                },
                "expected": {
                    "expires": dummy_time.time,
                    "permission_model": models.AppResourcePermission,
                },
            },
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": None,
                    "resource_ids": [fake_resource.id],
                    "dimension": "resource",
                },
                "expected": {
                    "expires": None,
                    "permission_model": models.AppResourcePermission,
                },
            },
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": 180,
                    "resource_ids": None,
                    "dimension": "api",
                },
                "expected": {
                    "expires": dummy_time.time,
                    "permission_model": models.AppAPIPermission,
                },
            },
            {
                "params": {
                    "bk_app_code": "apigw-test",
                    "expire_days": None,
                    "resource_ids": None,
                    "dimension": "api",
                },
                "expected": {
                    "expires": None,
                    "permission_model": models.AppAPIPermission,
                },
            },
        ]

        for test in data:
            response = request_view(
                "POST",
                "permissions.app-permissions",
                path_params={"gateway_id": fake_gateway.id},
                gateway=fake_gateway,
                data=test["params"],
            )
            result = response.json()
            assert result["code"] == 0, result


class TestAppPermissionBatchViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_renew(self):
        resource = G(Resource, api=self.gateway)

        perm_1 = G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test",
        )

        perm_2 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test",
            resource_id=resource.id,
            grant_type="apply",
        )

        data = [
            {
                "params": {"dimension": "api", "ids": [perm_1.id]},
            },
            {
                "params": {
                    "dimension": "resource",
                    "ids": [perm_2.id],
                },
            },
        ]

        for test in data:
            request = self.factory.post(
                f"/apis/{self.gateway.id}/permissions/app-permissions/batch/", data=test["params"]
            )

            view = views.AppPermissionBatchViewSet.as_view({"post": "renew"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0, result)

            permission_model = AppPermissionHelper().get_permission_model(test["params"]["dimension"])
            perm_record = permission_model.objects.filter(
                api=self.gateway,
                id=test["params"]["ids"][0],
            ).first()
            self.assertTrue(
                180 * 24 * 3600 - 10 < (perm_record.expires - now_datetime()).total_seconds() < 180 * 24 * 3600
            )

    def test_destroy(self):
        resource = G(Resource, api=self.gateway)

        perm_1 = G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test",
        )

        perm_2 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test",
            resource_id=resource.id,
            grant_type="apply",
        )

        data = [
            {
                "params": {
                    "dimension": "api",
                    "ids": [perm_1.id],
                },
            },
            {
                "params": {
                    "dimension": "resource",
                    "ids": [perm_2.id],
                },
            },
        ]

        for test in data:
            request = self.factory.delete(
                f"/apis/{self.gateway.id}/permissions/app-permissions/batch/", data=test["params"]
            )

            view = views.AppPermissionBatchViewSet.as_view({"delete": "destroy"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0, result)

            permission_model = AppPermissionHelper().get_permission_model(test["params"]["dimension"])
            self.assertFalse(
                permission_model.objects.filter(
                    api=self.gateway,
                    id=test["params"]["ids"][0],
                ).exists()
            )


class TestAppPermissionApplyViewSet:
    def test_list(self, request_factory, fake_gateway):
        G(
            models.AppPermissionApply,
            api=fake_gateway,
            bk_app_code="test",
        )

        data = [
            {
                "params": {
                    "bk_app_code": "test",
                    "applied_by": "",
                },
                "expected": {"count": 1},
            },
        ]

        for test in data:
            request = request_factory.get(
                f"/apis/{fake_gateway.id}/permissions/app-permission-apply/",
                data=test["params"],
            )

            view = views.AppPermissionApplyViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=fake_gateway.id)

            result = get_response_json(response)
            assert result["code"] == 0
            assert result["data"]["count"] == test["expected"]["count"]


class TestAppPermissionApplyBatchViewSet:
    def test_post(self, mocker, fake_gateway, request_factory):
        mocker.patch(
            "apigateway.apps.permission.helpers.APIPermissionDimensionManager.handle_permission_apply",
            return_value=mock.MagicMock(id=1),
        )
        mocker.patch(
            "apigateway.apps.permission.helpers.ResourcePermissionDimensionManager.handle_permission_apply",
            return_value=mock.MagicMock(id=1),
        )
        mocker.patch(
            "apigateway.apps.permission.views.send_mail_for_perm_handle",
            return_value=None,
        )

        apply_1 = G(
            models.AppPermissionApply,
            api=fake_gateway,
            grant_dimension="api",
        )

        apply_2 = G(
            models.AppPermissionApply,
            api=fake_gateway,
            _resource_ids="1,2,3",
            grant_dimension="resource",
        )

        data = [
            {
                "params": {
                    "ids": [apply_1.id],
                    "status": "approved",
                    "comment": "",
                },
            },
            {
                "params": {
                    "ids": [apply_2.id],
                    "status": "rejected",
                    "comment": "",
                    "part_resource_ids": {
                        f"{apply_2.id}": [2],
                    },
                },
            },
        ]

        for test in data:
            request = request_factory.post(
                f"/apis/{fake_gateway.id}/permissions/app-permission-apply/batch/",
                data=test["params"],
            )

            view = views.AppPermissionApplyBatchViewSet.as_view({"post": "post"})
            response = view(request, gateway_id=fake_gateway.id)
            result = get_response_json(response)

            assert result["code"] == 0

        assert models.AppPermissionApply.objects.filter(api=fake_gateway).count() == 0


class TestAppPermissionRecordViewSet(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.gateway = create_gateway()

    def test_list(self):
        resource = G(Resource, api=self.gateway)
        G(
            models.AppPermissionRecord,
            api=self.gateway,
            bk_app_code="test",
            _resource_ids=f"{resource.id}",
            _handled_resource_ids=json.dumps(
                {
                    "approved": [resource.id],
                    "rejected": [],
                }
            ),
        )
        data = [
            {
                "params": {
                    "bk_app_code": "test",
                },
                "expected": {
                    "count": 1,
                },
            },
        ]

        for test in data:
            request = self.factory.get(
                f"/apis/{self.gateway.id}/permissions/app-permission-records/", data=test["params"]
            )

            view = views.AppPermissionRecordViewSet.as_view({"get": "list"})
            response = view(request, gateway_id=self.gateway.id)

            result = get_response_json(response)
            self.assertEqual(result["code"], 0, result)
            self.assertEqual(result["data"]["count"], test["expected"]["count"])

    def test_retrieve(self):
        resource = G(Resource, api=self.gateway)
        record = G(
            models.AppPermissionRecord,
            api=self.gateway,
            bk_app_code="test",
            _resource_ids=f"{resource.id}",
            _handled_resource_ids=json.dumps(
                {
                    "approved": [resource.id],
                    "rejected": [],
                }
            ),
        )

        request = self.factory.get(f"/apis/{self.gateway.id}/permissions/app-permission-records/{record.id}/")

        view = views.AppPermissionRecordViewSet.as_view({"get": "retrieve"})
        response = view(request, gateway_id=self.gateway.id, id=record.id)

        result = get_response_json(response)
        self.assertEqual(result["code"], 0, result)
