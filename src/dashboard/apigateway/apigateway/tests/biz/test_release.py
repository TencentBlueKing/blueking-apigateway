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
    PublishSourceEnum,
    StageStatusEnum,
)
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, Stage


class TestReleaseHandler:
    def test_get_released_stage_ids(self, fake_gateway):
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()

        stage_1 = G(Stage, api=fake_gateway, status=StageStatusEnum.ACTIVE.value)
        G(Stage, api=fake_gateway, status=StageStatusEnum.INACTIVE.value)
        G(Release, gateway=fake_gateway, stage=stage_1)

        assert ReleaseHandler.get_released_stage_ids([fake_gateway.id]) == [stage_1.id]

        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()
        assert ReleaseHandler.get_released_stage_ids([fake_gateway.id]) == []

    def test_save_release_history(self, fake_release):
        ReleaseHandler.save_release_history(fake_release, PublishSourceEnum.VERSION_PUBLISH, "test")
        assert ReleaseHistory.objects.filter(gateway=fake_release.gateway, stage=fake_release.stage).count() == 1

    def test_get_latest_publish_event_by_release_history_ids(self):
        release_history = G(ReleaseHistory)
        event_1 = G(
            PublishEvent,
            publish=release_history,
            name=PublishEventNameTypeEnum.ValidateConfiguration.value,
            status=PublishEventStatusTypeEnum.DOING.value,
        )
        assert (
            ReleaseHandler.get_latest_publish_event_by_release_history_ids([release_history.id])[release_history.id]
            == event_1
        )

        event_2 = G(
            PublishEvent,
            publish=release_history,
            name=PublishEventNameTypeEnum.ValidateConfiguration.value,
            status=PublishEventStatusTypeEnum.SUCCESS.value,
        )
        assert (
            ReleaseHandler.get_latest_publish_event_by_release_history_ids([release_history.id])[release_history.id]
            == event_2
        )
