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
from ddf import G

from apigateway.apps.permission.models import (
    AppGatewayPermission,
    AppResourcePermission,
)
from apigateway.biz.permission import (
    ResourcePermissionHandler,
)
from apigateway.core.models import Gateway, Resource
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestResourcePermissionHandler:
    def test_grant_or_renewal_expire_soon(self, fake_gateway, fake_resource):
        data = [
            {
                "gateway": fake_gateway,
                "resource_id": fake_resource.id,
                "bk_app_code": "test",
            },
        ]
        for test in data:
            handler = ResourcePermissionHandler()
            handler.grant_or_renewal_expire_soon(test["gateway"], test["resource_id"], test["bk_app_code"], 1, 300)
            app_resource_permission = AppResourcePermission.objects.get_permission_or_none(
                gateway=test["gateway"],
                resource_id=test["resource_id"],
                bk_app_code=test["bk_app_code"],
            )
            assert not app_resource_permission.has_expired

    def test_sync_from_gateway_permission(self):
        bk_app_code = "test"
        gateway = G(Gateway)
        resource = G(Resource, gateway=gateway)

        # has no api-perm
        handler = ResourcePermissionHandler()
        handler.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert AppResourcePermission.objects.filter(gateway=gateway, bk_app_code=bk_app_code).count() == 0

        # api-perm expired
        api_perm = G(
            AppGatewayPermission,
            gateway=gateway,
            bk_app_code=bk_app_code,
            expires=now_datetime() - datetime.timedelta(seconds=10),
        )
        ResourcePermissionHandler.sync_from_gateway_permission(gateway, bk_app_code, [1])
        assert AppResourcePermission.objects.filter(gateway=gateway, bk_app_code=bk_app_code).count() == 0

        api_perm.expires = now_datetime() + datetime.timedelta(seconds=10)
        api_perm.save()
        ResourcePermissionHandler.sync_from_gateway_permission(gateway, bk_app_code, [resource.id])
        assert AppResourcePermission.objects.filter(gateway=gateway, bk_app_code=bk_app_code).count() == 1
