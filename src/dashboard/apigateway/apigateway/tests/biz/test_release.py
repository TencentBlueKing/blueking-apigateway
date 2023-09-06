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

from apigateway.biz.release import ReleaseHandler
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusTypeEnum,
    StageStatusEnum,
)
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, Stage


class TestReleaseHandler:
    def test_get_released_stage_ids(self, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage_1 = G(Stage, gateway=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        G(Stage, gateway=fake_gateway, status=StageStatusEnum.INACTIVE.value)
        G(Release, gateway=fake_gateway, stage=stage_1)

        assert ReleaseHandler.get_released_stage_ids([fake_gateway.id]) == [stage_1.id]

        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()
        assert ReleaseHandler.get_released_stage_ids([fake_gateway.id]) == []

    def test_get_latest_publish_event_by_release_history_ids(self, fake_release_history, fake_publish_event):
        assert (
            ReleaseHandler.get_latest_publish_event_by_release_history_ids([fake_release_history.id])[
                fake_release_history.id
            ]
            == fake_publish_event
        )

        event_2 = G(
            PublishEvent,
            publish=fake_release_history,
            name=PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value,
            status=PublishEventStatusTypeEnum.SUCCESS.value,
        )
        assert (
            ReleaseHandler.get_latest_publish_event_by_release_history_ids([fake_release_history.id])[
                fake_release_history.id
            ]
            == event_2
        )

    def test_batch_get_stage_release_status(self, fake_stage, fake_release_history, fake_publish_event):
        assert (
            ReleaseHandler.batch_get_stage_release_status([fake_stage.id])[fake_stage.id]["status"]
            == PublishEventStatusTypeEnum.DOING.value
        )
        fake_publish_event.status = PublishEventStatusTypeEnum.FAILURE.value
        fake_publish_event.save()

        assert (
            ReleaseHandler.batch_get_stage_release_status([fake_stage.id])[fake_stage.id]["status"]
            == PublishEventStatusTypeEnum.FAILURE.value
        )

        fake_publish_event.status = PublishEventStatusTypeEnum.SUCCESS.value
        fake_publish_event.save()

        assert (
            ReleaseHandler.batch_get_stage_release_status([fake_stage.id])[fake_stage.id]["status"]
            == PublishEventStatusTypeEnum.DOING.value
        )

        fake_publish_event.name = PublishEventNameTypeEnum.LOAD_CONFIGURATION.value
        fake_publish_event.status = PublishEventStatusTypeEnum.SUCCESS.value
        fake_publish_event.save()

        assert (
            ReleaseHandler.batch_get_stage_release_status([fake_stage.id])[fake_stage.id]["status"]
            == PublishEventStatusTypeEnum.SUCCESS.value
        )

    def test_delete_without_stage_related(self, fake_gateway):
        stage_1 = G(Stage, gateway=fake_gateway)
        stage_2 = G(Stage, gateway=fake_gateway)

        history_1 = G(ReleaseHistory, gateway=fake_gateway, stage=stage_1)
        history_2 = G(ReleaseHistory, gateway=fake_gateway, stage=stage_2)
        history_2.stages.add(stage_2)

        ReleaseHandler.delete_without_stage_related(fake_gateway.id)

        assert ReleaseHistory.objects.filter(id=history_1.id).exists() is False
