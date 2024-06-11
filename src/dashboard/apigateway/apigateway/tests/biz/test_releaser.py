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

import pytest
from ddf import G

from apigateway.biz.releaser import (
    BaseGatewayReleaser,
    MicroGatewayReleaseHistory,
    MicroGatewayReleaser,
    ReleaseError,
    ReleaseValidationError,
)
from apigateway.common.user_credentials import UserCredentials
from apigateway.core.constants import PublishEventEnum, PublishEventStatusEnum, ReleaseStatusEnum
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage

pytestmark = pytest.mark.django_db(transaction=True)


def get_release_data(gateway):
    stage = G(Stage, gateway=gateway)
    resource_version = G(
        ResourceVersion,
        gateway=gateway,
        name=f"{gateway.id}-{stage.id}",
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


class TestBaseGatewayReleaser:
    def test_from_data(self, fake_gateway, fake_stage, fake_resource_version):
        releaser = BaseGatewayReleaser.from_data(
            fake_gateway,
            fake_stage.id,
            fake_resource_version.id,
            "",
            user_credentials=UserCredentials(
                credentials="access_token",
            ),
        )
        assert isinstance(releaser, BaseGatewayReleaser)

        # 资源版本 不存在
        with pytest.raises(ResourceVersion.DoesNotExist):
            BaseGatewayReleaser.from_data(
                fake_gateway,
                fake_stage.id,
                0,
                "",
                user_credentials=UserCredentials(
                    credentials="access_token",
                ),
            )

    def test_release(self, mocker, fake_gateway, celery_mock_task):
        release_data = get_release_data(fake_gateway)
        releaser = BaseGatewayReleaser.from_data(
            fake_gateway,
            release_data["stage_id"],
            release_data["resource_version_id"],
            release_data.get("comment", ""),
            user_credentials=UserCredentials(
                credentials="access_token",
            ),
        )
        # 校验失败
        mocker.patch.object(releaser, "_validate", side_effect=ReleaseValidationError)
        with pytest.raises(ReleaseError):
            releaser.release()
        ReleaseHistory.objects.filter(gateway=fake_gateway, status=ReleaseStatusEnum.FAILURE.value).exists()
        # 校验成功
        mocker.patch.object(releaser, "_validate", return_value=None)
        mocker.patch.object(releaser, "_validate", return_value=None)
        mock_release = mocker.patch.object(releaser, "_do_release")
        # mock_post_release = mocker.patch.object(releaser, "_post_release")

        releaser.release()
        resource_version_ids = list(
            Release.objects.filter(stage_id=release_data["stage_id"])
            .distinct()
            .values_list("resource_version_id", flat=True)
        )
        assert len(resource_version_ids) == 1
        assert resource_version_ids[0] == release_data["resource_version_id"]
        # assert ReleaseHistory.objects.filter(gateway=fake_gateway, status=ReleaseStatusEnum.SUCCESS.value).exists()

        mock_release.assert_called()
        # mock_post_release.assert_called()


class TestMicroGatewayReleaser:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self, fake_gateway):
        self.gateway = fake_gateway
        release_data = get_release_data(self.gateway)
        # self.releaser = BaseGatewayReleaser.from_data(
        self.releaser = MicroGatewayReleaser.from_data(
            self.gateway,
            release_data["stage_id"],
            release_data["resource_version_id"],
            release_data["comment"],
            user_credentials=UserCredentials(
                credentials="access_token",
            ),
        )

    def test_do_release_edge_gateway(
        self,
        mocker,
        celery_task_eager_mode,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        fake_shared_gateway,
        fake_edge_gateway,
        fake_release,
        fake_release_history,
        fake_publish_success_event,
        celery_mock_task,
    ):
        mock_release_gateway_by_helm = mocker.patch(
            "apigateway.biz.releaser.release_gateway_by_helm",
            wraps=celery_mock_task,
        )
        releaser = MicroGatewayReleaser(
            gateway=fake_gateway,
            stage=fake_stage,
            resource_version=fake_resource_version,
            user_credentials=UserCredentials(
                credentials="access_token",
            ),
        )

        releaser._do_release(fake_release, fake_release_history)

        mock_release_gateway_by_helm.si.assert_called_once_with(
            release_id=fake_release.pk,
            micro_gateway_release_history_id=mocker.ANY,
            username=releaser.username,
            user_credentials={"bk_token": "access_token"},
        )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
        ).exists()

        qs = MicroGatewayReleaseHistory.objects.filter(
            gateway=fake_gateway,
            stage=fake_stage,
            release_history=fake_release_history,
        )

        assert qs.filter(micro_gateway=fake_edge_gateway).exists()

    def test_do_release_shared_gateway(
        self,
        mocker,
        celery_task_eager_mode,
        fake_gateway,
        fake_stage,
        fake_resource_version,
        fake_shared_gateway,
        fake_release,
        fake_release_history,
        fake_publish_success_event,
        celery_mock_task,
    ):
        mock_release_gateway_by_registry = mocker.patch(
            "apigateway.biz.releaser.release_gateway_by_registry",
            wraps=celery_mock_task,
        )
        releaser = MicroGatewayReleaser(gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

        releaser._do_release(fake_release, fake_release_history)

        mock_release_gateway_by_registry.si.assert_called_once_with(
            micro_gateway_id=fake_shared_gateway.id,
            release_id=fake_release.id,
            micro_gateway_release_history_id=mocker.ANY,
            publish_id=fake_release_history.id,
        )

        assert ReleaseHistory.objects.filter(
            id=fake_release_history.id,
        ).exists()

        assert MicroGatewayReleaseHistory.objects.filter(
            gateway=fake_gateway,
            stage=fake_stage,
            micro_gateway=fake_shared_gateway,
            release_history=fake_release_history,
        ).exists()
