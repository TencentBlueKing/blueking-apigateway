#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
from ddf import G
from django.test import override_settings

from apigateway.apps.permission.models import AppResourcePermission
from apigateway.controller.tasks.clean_task import delete_old_app_resource_permission_records
from apigateway.utils.time import to_datetime_from_now

pytestmark = pytest.mark.django_db


class TestDeleteOldAppResourcePermissionRecords:
    @override_settings(DEFAULT_TEST_APP={"bk_app_code": "default-test-app"})
    def test_delete_expired_records(self, fake_gateway):
        default_test_app_old_permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="default-test-app",
            resource_id=1,
            expires=to_datetime_from_now(days=-31),
        )
        default_test_app_recent_permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="default-test-app",
            resource_id=2,
            expires=to_datetime_from_now(days=-29),
        )
        other_app_old_permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="other-app",
            resource_id=3,
            expires=to_datetime_from_now(days=-(365 * 4)),
        )
        other_app_recent_permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="other-app",
            resource_id=4,
            expires=to_datetime_from_now(days=-31),
        )
        not_expired_permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="default-test-app",
            resource_id=5,
            expires=to_datetime_from_now(days=1),
        )
        permanent_permission = G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code="default-test-app",
            resource_id=6,
            expires=None,
        )

        delete_old_app_resource_permission_records()

        assert not AppResourcePermission.objects.filter(id=default_test_app_old_permission.id).exists()
        assert not AppResourcePermission.objects.filter(id=other_app_old_permission.id).exists()
        assert AppResourcePermission.objects.filter(id=default_test_app_recent_permission.id).exists()
        assert AppResourcePermission.objects.filter(id=other_app_recent_permission.id).exists()
        assert AppResourcePermission.objects.filter(id=not_expired_permission.id).exists()
        assert AppResourcePermission.objects.filter(id=permanent_permission.id).exists()
