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

from datetime import timedelta

import pytest
from ddf import G
from django.test import override_settings
from django.utils import timezone

from apigateway.apps.data_plane.models import DataPlane
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.biz.release import ReleaseHandler
from apigateway.controller.tasks.clean_task import (
    delete_old_app_resource_permission_records,
    delete_old_publish_events,
)
from apigateway.core.models import PublishEvent, ReleaseHistory, Stage
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


@override_settings(CLEAN_TABLE_INTERVAL_DAYS=365)
def test_publish_cleanup_preserves_latest_history_per_stage_and_data_plane(fake_gateway, fake_stage):
    old_time = timezone.now() - timedelta(days=400)
    retained_ids = set()
    deleted_ids = set()
    recent_ids = set()
    stages = [fake_stage, G(Stage, gateway=fake_gateway)]
    planes = [None, G(DataPlane), G(DataPlane)]
    for stage in stages:
        for plane in planes:
            old_history = G(ReleaseHistory, gateway=fake_gateway, stage=stage, data_plane=plane)
            deleted_ids.add(G(PublishEvent, publish=old_history, created_time=old_time).id)
            recent_ids.add(G(PublishEvent, publish=old_history, created_time=timezone.now()).id)
            latest = G(ReleaseHistory, gateway=fake_gateway, stage=stage, data_plane=plane, created_time=old_time)
            for step, name in [(0, "validata_configuration"), (5, "load_configuration")]:
                retained_ids.add(
                    G(
                        PublishEvent,
                        gateway=fake_gateway,
                        stage=stage,
                        publish=latest,
                        step=step,
                        name=name,
                        status="success",
                        created_time=old_time,
                    ).id
                )

    delete_old_publish_events()

    assert set(PublishEvent.objects.values_list("id", flat=True)) == retained_ids | recent_ids
    assert not PublishEvent.objects.filter(id__in=deleted_ids).exists()
    assert all(
        item["status"] == "success"
        for item in ReleaseHandler.batch_get_stage_release_status([stage.id for stage in stages]).values()
    )
    # Once a newer publish exists, the formerly protected expired events can be cleaned.
    for stage in stages:
        for plane in planes:
            G(ReleaseHistory, gateway=fake_gateway, stage=stage, data_plane=plane)
    delete_old_publish_events()
    assert set(PublishEvent.objects.values_list("id", flat=True)) == recent_ids
