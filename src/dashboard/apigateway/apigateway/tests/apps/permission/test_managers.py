# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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
from django_dynamic_fixture import G

from apigateway.apps.permission import models
from apigateway.apps.permission.constants import PermissionApplyExpireDaysEnum
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
        gateway_1 = G(Gateway, is_public=True)
        gateway_2 = G(Gateway, is_public=False)

        G(models.AppGatewayPermission, gateway=gateway_1, bk_app_code=unique_id)
        G(models.AppGatewayPermission, gateway=gateway_2, bk_app_code=unique_id)

        assert models.AppGatewayPermission.objects.filter_public_permission_by_app(unique_id).count() == 1

    def test_renew_by_ids(self):
        perm_1 = G(
            models.AppGatewayPermission,
            gateway=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
        )
        perm_2 = G(
            models.AppGatewayPermission,
            gateway=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(170),
        )
        perm_3 = G(
            models.AppGatewayPermission,
            gateway=self.gateway,
            bk_app_code="test-3",
            expires=to_datetime_from_now(days=720),
        )

        models.AppGatewayPermission.objects.renew_by_ids(
            self.gateway,
            ids=[perm_1.id, perm_2.id, perm_3.id],
        )
        perm_1 = models.AppGatewayPermission.objects.get(id=perm_1.id)
        perm_2 = models.AppGatewayPermission.objects.get(id=perm_2.id)
        perm_3 = models.AppGatewayPermission.objects.get(id=perm_3.id)
        assert to_datetime_from_now(days=179) < perm_1.expires < to_datetime_from_now(days=181)
        assert to_datetime_from_now(days=170 + 179) < perm_2.expires < to_datetime_from_now(days=170 + 181)
        assert to_datetime_from_now(days=720 + 179) < perm_3.expires < to_datetime_from_now(days=720 + 181)


class TestAppResourcePermissionManager:
    @pytest.fixture(autouse=True)
    def setup_fixture(self):
        self.gateway = G(Gateway, created_by="admin")
        self.resource = G(Resource, gateway=self.gateway)

    def test_filter_public_permission_by_app(self, unique_id):
        gateway_1 = G(Gateway, is_public=True)
        gateway_2 = G(Gateway, is_public=False)

        G(models.AppResourcePermission, gateway=gateway_1, bk_app_code=unique_id)
        G(models.AppResourcePermission, gateway=gateway_2, bk_app_code=unique_id)

        assert models.AppResourcePermission.objects.filter_public_permission_by_app(unique_id).count() == 1

    def test_renew_by_ids(self):
        perm_1 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
            resource_id=self.resource.id,
        )
        perm_2 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(days=70),
            resource_id=self.resource.id,
        )
        perm_3 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-3",
            expires=to_datetime_from_now(days=720),
            resource_id=self.resource.id,
        )

        models.AppResourcePermission.objects.renew_by_ids(
            self.gateway,
            ids=[perm_1.id, perm_2.id, perm_3.id],
        )
        perm_1 = models.AppResourcePermission.objects.get(id=perm_1.id)
        perm_2 = models.AppResourcePermission.objects.get(id=perm_2.id)
        perm_3 = models.AppResourcePermission.objects.get(id=perm_3.id)
        assert to_datetime_from_now(days=179) < perm_1.expires < to_datetime_from_now(181)
        assert to_datetime_from_now(days=70 + 179) < perm_2.expires < to_datetime_from_now(70 + 181)
        assert to_datetime_from_now(days=720 + 179) < perm_3.expires < to_datetime_from_now(720 + 181)

    def test_renew_by_resource_ids(self):
        perm_1 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
            resource_id=self.resource.id,
        )
        perm_2 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(days=70),
            resource_id=self.resource.id,
        )
        perm_3 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-3",
            expires=to_datetime_from_now(days=720),
            resource_id=self.resource.id,
        )

        models.AppResourcePermission.objects.renew_by_resource_ids(
            self.gateway,
            perm_1.bk_app_code,
            resource_ids=[perm_1.resource_id],
            # 永久
            expire_days=PermissionApplyExpireDaysEnum.FOREVER.value,
        )
        models.AppResourcePermission.objects.renew_by_resource_ids(
            self.gateway,
            perm_2.bk_app_code,
            resource_ids=[perm_2.resource_id],
            # 360天
            expire_days=PermissionApplyExpireDaysEnum.TWELVE_MONTH.value,
        )
        models.AppResourcePermission.objects.renew_by_resource_ids(
            self.gateway,
            perm_3.bk_app_code,
            resource_ids=[perm_3.resource_id],
            # 180天
            expire_days=PermissionApplyExpireDaysEnum.SIX_MONTH.value,
        )
        perm_1 = models.AppResourcePermission.objects.get(id=perm_1.id)
        perm_2 = models.AppResourcePermission.objects.get(id=perm_2.id)
        perm_3 = models.AppResourcePermission.objects.get(id=perm_3.id)
        assert perm_1.expires > to_datetime_from_now(181)
        assert to_datetime_from_now(days=70 + 359) < perm_2.expires < to_datetime_from_now(70 + 361)
        assert to_datetime_from_now(days=720 + 179) < perm_3.expires < to_datetime_from_now(720 + 181)

    def test_renew_not_expired_permission(self):
        perm_1 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-1",
            expires=dummy_time.time,
            resource_id=self.resource.id,
        )
        perm_2 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
            bk_app_code="test-2",
            expires=to_datetime_from_now(days=70),
            resource_id=self.resource.id,
        )
        perm_3 = G(
            models.AppResourcePermission,
            gateway=self.gateway,
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
        resource_1 = G(Resource, gateway=self.gateway)
        resource_2 = G(Resource, gateway=self.gateway)
        G(
            models.AppResourcePermission,
            gateway=self.gateway,
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
                gateway=self.gateway, resource_id=test["resource_ids"][0], bk_app_code=test["bk_app_code"]
            )
            assert permission.grant_type == test["grant_type"]
            assert 180 * 24 * 3600 - 10 < (permission.expires - now_datetime()).total_seconds() < 180 * 24 * 3600


class TestAppPermissionRecordManager:
    def test_filter_record(self):
        gateway_1 = G(Gateway, name="test1")
        gateway_2 = G(Gateway, name="test2")

        G(
            models.AppPermissionRecord,
            gateway=gateway_1,
            bk_app_code="test",
            applied_by="admin1",
            applied_time=now_datetime(),
            handled_time=now_datetime(),
            status="pending",
            grant_dimension="api",
        )
        G(
            models.AppPermissionRecord,
            gateway=gateway_2,
            bk_app_code="test-2",
            applied_by="admin2",
            applied_time=dummy_time.time,
            handled_time=dummy_time.time,
            status="approved",
            grant_dimension="resource",
        )

        queryset = models.AppPermissionRecord.objects.filter(gateway__id__in=[gateway_1.id, gateway_2.id])
        assert models.AppPermissionRecord.objects.filter_record(queryset, bk_app_code="test").count() == 1
        assert (
            models.AppPermissionRecord.objects.filter_record(
                queryset,
                applied_time_start=now_datetime() - datetime.timedelta(seconds=10),
                applied_time_end=now_datetime() + datetime.timedelta(seconds=10),
            ).count()
            == 1
        )
        assert models.AppPermissionRecord.objects.filter_record(queryset, status="approved").count() == 1
