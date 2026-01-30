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
import json

import pytest
from ddf import G

from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.biz.gateway import (
    GatewayReleaser,
    ReleaseError,
    ReleaseValidationError,
)
from apigateway.core.constants import PublishEventEnum, PublishEventStatusEnum
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage

pytestmark = pytest.mark.django_db(transaction=True)


def get_release_data(gateway):
    stage = G(Stage, gateway=gateway)
    resource_version = G(
        ResourceVersion,
        gateway=gateway,
        _data=json.dumps([{"id": 1, "name": "demo", "method": "GET", "path": "/"}]),
    )
    G(
        ReleaseHistory,
        gateway=gateway,
        stage=stage,
        resource_version=resource_version,
    )
    G(
        PublishEvent,
        gateway=gateway,
        stage=stage,
        name=PublishEventEnum.LOAD_CONFIGURATION.value,
        status=PublishEventStatusEnum.SUCCESS.value,
        step=5,
    )
    return {
        "stage_id": stage.id,
        "resource_version_id": resource_version.id,
        "comment": "",
    }


class TestGatewayReleaserBase:
    def test_from_data(self, fake_gateway, fake_stage, fake_resource_version):
        releaser = GatewayReleaser.from_data(
            fake_gateway,
            fake_stage.id,
            fake_resource_version.id,
            "",
        )
        assert isinstance(releaser, GatewayReleaser)

        # 资源版本 不存在
        with pytest.raises(ResourceVersion.DoesNotExist):
            GatewayReleaser.from_data(
                fake_gateway,
                fake_stage.id,
                0,
                "",
            )

    def test_release(self, mocker, fake_gateway, celery_mock_task):
        # Setup data plane binding for the gateway
        data_plane = G(DataPlane, name="default")
        G(GatewayDataPlaneBinding, gateway=fake_gateway, data_plane=data_plane)

        release_data = get_release_data(fake_gateway)
        releaser = GatewayReleaser.from_data(
            fake_gateway,
            release_data["stage_id"],
            release_data["resource_version_id"],
            release_data.get("comment", ""),
        )
        # 校验失败
        mocker.patch.object(releaser, "_validate", side_effect=ReleaseValidationError)
        with pytest.raises(ReleaseError):
            releaser.release()
        ReleaseHistory.objects.filter(gateway=fake_gateway).exists()
        # 校验成功
        mocker.patch.object(releaser, "_validate", return_value=None)
        mocker.patch.object(releaser, "_validate", return_value=None)
        mock_release = mocker.patch.object(releaser, "_do_release")

        releaser.release()
        resource_version_ids = list(
            Release.objects.filter(stage_id=release_data["stage_id"])
            .distinct()
            .values_list("resource_version_id", flat=True)
        )
        assert len(resource_version_ids) == 1
        assert resource_version_ids[0] == release_data["resource_version_id"]

        mock_release.assert_called()
        # mock_post_release.assert_called()


class TestGatewayReleaser:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_gateway):
        self.gateway = fake_gateway
        release_data = get_release_data(self.gateway)
        self.releaser = GatewayReleaser.from_data(
            self.gateway,
            release_data["stage_id"],
            release_data["resource_version_id"],
            release_data["comment"],
        )

    def test_do_release(
        self,
        mocker,
        celery_task_eager_mode,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        fake_release,
        fake_release_history,
        fake_publish_success_event,
        celery_mock_task,
    ):
        mock_release_gateway_by_registry = mocker.patch(
            "apigateway.biz.gateway.releaser.release_gateway_by_registry",
            wraps=celery_mock_task,
        )
        releaser = GatewayReleaser(gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

        # Create data plane for the test
        data_plane = G(DataPlane, name="default")

        releaser._do_release(fake_release, fake_release_history, data_plane)

        mock_release_gateway_by_registry.si.assert_called_once_with(
            publish_id=fake_release_history.id,
            data_plane_id=data_plane.id,
        )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
        ).exists()
