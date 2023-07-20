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
from ddf import G

from apigateway.apps.metrics.models import StatisticsAppRequestByDay
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.apps.permission.tasks import renew_app_resource_permission
from apigateway.utils.time import now_datetime, to_datetime_from_now


class TestRenewAppResourcePermission:
    def test(self, fake_gateway, unique_id):
        bk_app_code = unique_id
        now = now_datetime()

        G(
            StatisticsAppRequestByDay,
            api_id=fake_gateway.id,
            bk_app_code=bk_app_code,
            resource_id=1,
            end_time=to_datetime_from_now(days=-3),
        )
        G(StatisticsAppRequestByDay, api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=2, end_time=now)
        G(StatisticsAppRequestByDay, api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=3, end_time=now)
        G(StatisticsAppRequestByDay, api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=4, end_time=now)
        G(StatisticsAppRequestByDay, api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=5, end_time=now)

        G(
            AppResourcePermission,
            api=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=1,
            expires=to_datetime_from_now(days=3),
        )
        G(
            AppResourcePermission,
            api=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=2,
            expires=to_datetime_from_now(days=-3),
        )
        G(
            AppResourcePermission,
            api=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=3,
            expires=to_datetime_from_now(days=3),
        )
        G(
            AppResourcePermission,
            api=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=4,
            expires=to_datetime_from_now(days=720),
        )
        G(
            AppResourcePermission,
            api=fake_gateway,
            bk_app_code=bk_app_code,
            resource_id=5,
            expires=to_datetime_from_now(days=170),
        )

        renew_app_resource_permission()

        assert AppResourcePermission.objects.get(
            api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=1
        ).expires < to_datetime_from_now(days=4)
        assert (
            AppResourcePermission.objects.get(api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=2).expires
            < now_datetime()
        )
        assert AppResourcePermission.objects.get(
            api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=3
        ).expires > to_datetime_from_now(days=179)
        assert AppResourcePermission.objects.get(
            api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=4
        ).expires > to_datetime_from_now(days=719)
        assert AppResourcePermission.objects.get(
            api_id=fake_gateway.id, bk_app_code=bk_app_code, resource_id=5
        ).expires > to_datetime_from_now(days=179)
