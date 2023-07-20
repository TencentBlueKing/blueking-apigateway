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
import datetime

import pytest
from django.test import TestCase
from django_dynamic_fixture import G

from apigateway.apps.permission import models
from apigateway.core.models import Gateway, Resource
from apigateway.tests.utils.testing import dummy_time
from apigateway.utils.time import now_datetime, to_datetime_from_now

# from apigateway.apps.permission import constants

pytestmark = pytest.mark.django_db


class TestAppAPIPermissionManager:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway, created_by="admin")

    def test_filter_public_permission_by_app(self, unique_id):
        api1 = G(Gateway, is_public=True)
        api2 = G(Gateway, is_public=False)

        G(models.AppAPIPermission, api=api1, bk_app_code=unique_id)
        G(models.AppAPIPermission, api=api2, bk_app_code=unique_id)

        assert 1 == models.AppAPIPermission.objects.filter_public_permission_by_app(unique_id).count()

    def test_filter_permission(self):
        G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test",
        )
        G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test-2",
        )

        data = [
            {
                "params": {},
                "expected": {
                    "count": 2,
                },
            },
            {
                "params": {
                    "bk_app_code": "test",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "bk_app_code": "test",
                    "grant_type": "initialize",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "bk_app_code": "test",
                    "grant_type": "apply",
                },
                "expected": {
                    "count": 0,
                },
            },
            {
                "params": {
                    "bk_app_codes": ["test-2", "test", "not-exist"],
                },
                "expected": {
                    "count": 2,
                },
            },
        ]

        for test in data:
            queryset = models.AppAPIPermission.objects.filter_permission(self.gateway, **test["params"])
            assert queryset.count() == test["expected"]["count"]

    def test_renew_permission(self):
        perm_1 = G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
        )
        perm_2 = G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(170),
        )
        perm_3 = G(
            models.AppAPIPermission,
            api=self.gateway,
            bk_app_code="test-3",
            expires=to_datetime_from_now(days=720),
        )

        models.AppAPIPermission.objects.renew_permission(
            self.gateway,
            ids=[perm_1.id, perm_2.id, perm_3.id],
        )
        perm_1 = models.AppAPIPermission.objects.get(id=perm_1.id)
        perm_2 = models.AppAPIPermission.objects.get(id=perm_2.id)
        perm_3 = models.AppAPIPermission.objects.get(id=perm_3.id)
        assert to_datetime_from_now(days=179) < perm_1.expires < to_datetime_from_now(days=181)
        assert to_datetime_from_now(days=179) < perm_2.expires < to_datetime_from_now(days=181)
        assert to_datetime_from_now(days=719) < perm_3.expires < to_datetime_from_now(days=721)

    def test_delete_permission(self, fake_gateway):
        p1 = G(models.AppAPIPermission, api=fake_gateway, bk_app_code="app1")
        p2 = G(models.AppAPIPermission, api=fake_gateway, bk_app_code="app2")
        G(models.AppAPIPermission, api=fake_gateway, bk_app_code="app3")
        G(models.AppAPIPermission, api=fake_gateway, bk_app_code="app4")

        models.AppAPIPermission.objects.delete_permission(fake_gateway, ids=[p1.id])
        assert not models.AppAPIPermission.objects.filter(api=fake_gateway, id=p1.id).exists()
        assert models.AppAPIPermission.objects.filter(api=fake_gateway, id=p2.id).exists()

        models.AppAPIPermission.objects.delete_permission(fake_gateway, bk_app_codes=["app2", "app3"])
        assert not models.AppAPIPermission.objects.filter(api=fake_gateway, bk_app_code__in=["app2", "app3"]).exists()
        assert models.AppAPIPermission.objects.filter(api=fake_gateway, bk_app_code="app4").exists()


class TestAppResourcePermissionManager:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway, created_by="admin")
        self.resource = G(Resource, api=self.gateway)

    def test_filter_public_permission_by_app(self, unique_id):
        api1 = G(Gateway, is_public=True)
        api2 = G(Gateway, is_public=False)

        G(models.AppResourcePermission, api=api1, bk_app_code=unique_id)
        G(models.AppResourcePermission, api=api2, bk_app_code=unique_id)

        assert 1 == models.AppResourcePermission.objects.filter_public_permission_by_app(unique_id).count()

    def test_filter_permission(self):
        G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test",
            grant_type="initialize",
            resource_id=self.resource.id,
        )
        G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-2",
            grant_type="apply",
            resource_id=self.resource.id,
        )

        data = [
            {
                "params": {},
                "expected": {
                    "count": 2,
                },
            },
            {
                "params": {
                    "bk_app_code": "test",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "bk_app_code": "test",
                    "grant_type": "initialize",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "bk_app_code": "test-2",
                    "grant_type": "apply",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "resource_ids": [self.resource.id],
                },
                "expected": {
                    "count": 2,
                },
            },
            {
                "params": {
                    "bk_app_codes": ["test", "test-2"],
                },
                "expected": {
                    "count": 2,
                },
            },
        ]

        for test in data:
            queryset = models.AppResourcePermission.objects.filter_permission(self.gateway, **test["params"])
            assert queryset.count() == test["expected"]["count"]

    def test_renew_permission(self):
        perm_1 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
            resource_id=self.resource.id,
        )
        perm_2 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(days=70),
            resource_id=self.resource.id,
        )
        perm_3 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-3",
            expires=to_datetime_from_now(days=720),
            resource_id=self.resource.id,
        )

        models.AppResourcePermission.objects.renew_permission(
            self.gateway,
            ids=[perm_1.id, perm_2.id, perm_3.id],
        )
        perm_1 = models.AppResourcePermission.objects.get(id=perm_1.id)
        perm_2 = models.AppResourcePermission.objects.get(id=perm_2.id)
        perm_3 = models.AppResourcePermission.objects.get(id=perm_3.id)
        assert to_datetime_from_now(days=179) < perm_1.expires < to_datetime_from_now(181)
        assert to_datetime_from_now(days=179) < perm_2.expires < to_datetime_from_now(181)
        assert to_datetime_from_now(days=719) < perm_3.expires < to_datetime_from_now(721)

    def test_renew_not_expired_permission(self):
        perm_1 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
            resource_id=self.resource.id,
        )
        perm_2 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(days=70),
            resource_id=self.resource.id,
        )
        perm_3 = G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test-3",
            expires=to_datetime_from_now(days=720),
            resource_id=self.resource.id,
        )

        for bk_app_code in ["test-1", "test-2", "test-3"]:
            models.AppResourcePermission.objects.renew_not_expired_permissions(
                self.gateway,
                bk_app_code=bk_app_code,
                resource_ids=[self.resource.id],
            )
        perm_1 = models.AppResourcePermission.objects.get(id=perm_1.id)
        perm_2 = models.AppResourcePermission.objects.get(id=perm_2.id)
        perm_3 = models.AppResourcePermission.objects.get(id=perm_3.id)
        assert perm_1.expires == dummy_time.time
        assert to_datetime_from_now(days=179) < perm_2.expires < to_datetime_from_now(181)
        assert to_datetime_from_now(days=719) < perm_3.expires < to_datetime_from_now(721)

    def test_save_permissions(self):
        resource_1 = G(Resource, api=self.gateway)
        resource_2 = G(Resource, api=self.gateway)
        G(
            models.AppResourcePermission,
            api=self.gateway,
            bk_app_code="test",
            grant_type="initialize",
            resource_id=resource_1.id,
        )

        data = [
            {
                "resource_ids": [resource_1.id],
                "bk_app_code": "test",
                "grant_type": "apply",
                "expire_days": 180,
            },
            {
                "resource_ids": [resource_2.id],
                "bk_app_code": "test",
                "grant_type": "apply",
                "expire_days": 180,
            },
        ]
        for test in data:
            models.AppResourcePermission.objects.save_permissions(self.gateway, **test)
            permission = models.AppResourcePermission.objects.get(
                api=self.gateway, resource_id=test["resource_ids"][0], bk_app_code=test["bk_app_code"]
            )
            assert permission.grant_type == test["grant_type"]
            assert 180 * 24 * 3600 - 10 < (permission.expires - now_datetime()).total_seconds() < 180 * 24 * 3600

    def test_sync_from_api_permission(self):
        bk_app_code = "test"
        gateway = G(Gateway)
        resource = G(Resource, api=gateway)

        # has no api-perm
        models.AppResourcePermission.objects.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert models.AppResourcePermission.objects.filter(api=gateway, bk_app_code=bk_app_code).count() == 0

        # api-perm expired
        api_perm = G(
            models.AppAPIPermission,
            api=gateway,
            bk_app_code=bk_app_code,
            expires=now_datetime() - datetime.timedelta(seconds=10),
        )
        models.AppResourcePermission.objects.sync_from_gateway_permission(gateway, bk_app_code, [1])
        assert models.AppResourcePermission.objects.filter(api=gateway, bk_app_code=bk_app_code).count() == 0

        api_perm.expires = now_datetime() + datetime.timedelta(seconds=10)
        api_perm.save()
        models.AppResourcePermission.objects.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert models.AppResourcePermission.objects.filter(api=gateway, bk_app_code=bk_app_code).count() == 1

    def test_delete_permission(self, fake_gateway):
        resource = G(Resource, api=fake_gateway)
        p1 = G(models.AppResourcePermission, api=fake_gateway, bk_app_code="app1", resource_id=resource.id)
        p2 = G(models.AppResourcePermission, api=fake_gateway, bk_app_code="app2", resource_id=resource.id)
        G(models.AppResourcePermission, api=fake_gateway, bk_app_code="app3", resource_id=resource.id)
        G(models.AppResourcePermission, api=fake_gateway, bk_app_code="app4", resource_id=resource.id)

        models.AppResourcePermission.objects.delete_permission(fake_gateway, ids=[p1.id])
        assert not models.AppResourcePermission.objects.filter(api=fake_gateway, id=p1.id).exists()
        assert models.AppResourcePermission.objects.filter(api=fake_gateway, id=p2.id).exists()

        models.AppResourcePermission.objects.delete_permission(fake_gateway, bk_app_codes=["app2", "app3"])
        assert not models.AppResourcePermission.objects.filter(
            api=fake_gateway, bk_app_code__in=["app2", "app3"]
        ).exists()
        assert models.AppResourcePermission.objects.filter(api=fake_gateway, bk_app_code="app4").exists()


class TestAppPermissionApplyManager(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gateway = G(Gateway)

    def test_filter_apply(self):
        G(
            models.AppPermissionApply,
            api=self.gateway,
            bk_app_code="test",
            applied_by="admin",
        )
        G(
            models.AppPermissionApply,
            api=self.gateway,
            bk_app_code="test-2",
            applied_by="admin-2",
        )

        data = [
            {
                "params": {},
                "expected": {
                    "count": 2,
                },
            },
            {
                "params": {
                    "bk_app_code": "test",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "applied_by": "admin-2",
                },
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            queryset = models.AppPermissionApply.objects.filter(api=self.gateway)
            queryset = models.AppPermissionApply.objects.filter_apply(queryset, **test["params"])
            self.assertEqual(queryset.count(), test["expected"]["count"])


class TestAppPermissionRecordManager:
    def test_filter_record(self):
        api1 = G(Gateway, name="test1")
        api2 = G(Gateway, name="test2")

        G(
            models.AppPermissionRecord,
            api=api1,
            bk_app_code="test",
            applied_by="admin1",
            applied_time=now_datetime(),
            handled_time=now_datetime(),
            status="pending",
            grant_dimension="api",
        )
        G(
            models.AppPermissionRecord,
            api=api2,
            bk_app_code="test-2",
            applied_by="admin2",
            applied_time=dummy_time.time,
            handled_time=dummy_time.time,
            status="approved",
            grant_dimension="resource",
        )

        queryset = models.AppPermissionRecord.objects.filter(api__id__in=[api1.id, api2.id])
        assert 1 == models.AppPermissionRecord.objects.filter_record(queryset, bk_app_code="test").count()
        assert (
            1
            == models.AppPermissionRecord.objects.filter_record(
                queryset,
                handled_time_start=now_datetime() - datetime.timedelta(seconds=10),
                handled_time_end=now_datetime() + datetime.timedelta(seconds=10),
            ).count()
        )
        assert (
            1
            == models.AppPermissionRecord.objects.filter_record(
                queryset,
                applied_time_start=now_datetime() - datetime.timedelta(seconds=10),
                applied_time_end=now_datetime() + datetime.timedelta(seconds=10),
            ).count()
        )
        assert (
            1
            == models.AppPermissionRecord.objects.filter_record(
                queryset,
                grant_dimension="api",
            ).count()
        )
        assert 1 == models.AppPermissionRecord.objects.filter_record(queryset, status="approved").count()
