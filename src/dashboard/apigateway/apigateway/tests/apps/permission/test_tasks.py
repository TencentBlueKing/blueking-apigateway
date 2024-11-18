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
import json

from ddf import G
from django.utils import timezone

from apigateway.apps.metrics.models import StatisticsAppRequestByDay
from apigateway.apps.permission.models import AppGatewayPermission, AppResourcePermission
from apigateway.apps.permission.tasks import AppPermissionExpiringSoonAlerter, renew_app_resource_permission
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Context, Resource
from apigateway.utils.time import now_datetime, to_datetime_from_now


class TestRenewAppResourcePermission:
    def test(self, fake_gateway, unique_id):
        bk_app_code = unique_id
        now = now_datetime()

        G(
            StatisticsAppRequestByDay,
            gateway_id=fake_gateway.id,
            bk_app_code=bk_app_code,
            resource_id=1,
            end_time=to_datetime_from_now(days=-3),
        )
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=2, end_time=now)
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=3, end_time=now)
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=4, end_time=now)
        G(StatisticsAppRequestByDay, gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=5, end_time=now)

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=1,
            expires=to_datetime_from_now(days=3),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=2,
            expires=to_datetime_from_now(days=-3),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=3,
            expires=to_datetime_from_now(days=3),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=4,
            expires=to_datetime_from_now(days=720),
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=5,
            expires=to_datetime_from_now(days=170),
        )

        renew_app_resource_permission()

        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=1
        ).expires < to_datetime_from_now(days=4)
        assert (
            AppResourcePermission.objects.get(
                gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=2
            ).expires
            < now_datetime()
        )
        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=3
        ).expires > to_datetime_from_now(days=179)
        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=4
        ).expires > to_datetime_from_now(days=719)
        assert AppResourcePermission.objects.get(
            gateway_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=5
        ).expires > to_datetime_from_now(days=179)


class TestAppPermissionExpiringSoonAlerter:
    def test_get_permissions_expiring_soon(self, fake_gateway, unique_id):
        now = timezone.now()
        G(AppGatewayPermission, gateway=fake_gateway, expires=now + datetime.timedelta(days=20), bk_app_code=unique_id)

        resource1 = G(Resource, gateway=fake_gateway, allow_apply_permission=True)
        resource2 = G(Resource, gateway=fake_gateway, allow_apply_permission=True)
        resource3 = G(Resource, gateway=fake_gateway, allow_apply_permission=True)
        resource4 = G(Resource, gateway=fake_gateway, allow_apply_permission=True)

        G(
            Context,
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            type=ContextTypeEnum.RESOURCE_AUTH.value,
            scope_id=resource1.id,
            _config=json.dumps({
                "resource_perm_required": True,
            }),
        )
        G(
            Context,
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            type=ContextTypeEnum.RESOURCE_AUTH.value,
            scope_id=resource2.id,
            _config=json.dumps({
                "resource_perm_required": True,
            }),
        )
        G(
            Context,
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            type=ContextTypeEnum.RESOURCE_AUTH.value,
            scope_id=resource3.id,
            _config=json.dumps({
                "resource_perm_required": True,
            }),
        )
        G(
            Context,
            scope_type=ContextScopeTypeEnum.RESOURCE.value,
            type=ContextTypeEnum.RESOURCE_AUTH.value,
            scope_id=resource4.id,
            _config=json.dumps({
                "resource_perm_required": False,
            }),
        )

        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource1.id,
            expires=now + datetime.timedelta(days=10),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource2.id,
            expires=now + datetime.timedelta(days=70),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource3.id,
            expires=now + datetime.timedelta(days=15),
            bk_app_code="test2",
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            resource_id=resource4.id,
            expires=now + datetime.timedelta(days=15),
            bk_app_code="test2",
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [])
        result = alerter._get_permissions_expiring_soon()
        assert len(result[unique_id]) == 2
        assert len(result["test2"]) == 1

    def test_filter_permissions(self, fake_gateway, unique_id):
        now = timezone.now()
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            expires=now + datetime.timedelta(hours=24 * 1 + 1),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            expires=now + datetime.timedelta(hours=24 * 3 + 2),
            bk_app_code=unique_id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            expires=now + datetime.timedelta(hours=24 * 7 + 1),
            bk_app_code=unique_id,
        )

        alerter = AppPermissionExpiringSoonAlerter(30, [1, 3])

        permissions = alerter._get_permissions_expiring_soon()
        assert len(permissions[unique_id]) == 3

        result = alerter._filter_permissions(permissions)
        assert len(result[unique_id]) == 2

        fake_gateway.status = 0
        fake_gateway.save()

        result = alerter._filter_permissions(permissions)
        assert len(result.get(unique_id, [])) == 0

    def test_complete_permissions(self, fake_gateway, unique_id):
        now = timezone.now()
        G(AppResourcePermission, gateway=fake_gateway, expires=now + datetime.timedelta(days=1), bk_app_code=unique_id)
        G(AppResourcePermission, gateway=fake_gateway, expires=now + datetime.timedelta(days=2), bk_app_code=unique_id)
        G(AppResourcePermission, gateway=fake_gateway, expires=now + datetime.timedelta(days=3), bk_app_code=unique_id)

        alerter = AppPermissionExpiringSoonAlerter(30, [])

        permissions = alerter._get_permissions_expiring_soon()
        alerter._complete_permissions(permissions)
        assert permissions[unique_id][0]["gateway_name"] == fake_gateway.name
