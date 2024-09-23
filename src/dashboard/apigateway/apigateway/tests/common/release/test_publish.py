#  -*- coding: utf-8 -*-
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
import pytest
from django.conf import settings

from apigateway.controller.publisher.publish import (
    _is_gateway_ok_for_releasing,
    _save_release_history,
    _trigger_revoke_publish_for_disable,
    _trigger_rolling_publish,
)
from apigateway.core.constants import GatewayStatusEnum, PublishSourceEnum, StageStatusEnum


class TestTriggerGatewayPublish:
    @pytest.fixture(autouse=True)
    def setup(self, mocker):
        self.distributor = mocker.MagicMock()
        mocker.patch("apigateway.controller.tasks.syncing.CombineDistributor", return_value=self.distributor)

    def test__is_gateway_ok_for_releasing_with_none_release(self):
        release = None
        source = PublishSourceEnum.BACKEND_UPDATE
        ok, msg = _is_gateway_ok_for_releasing(release, source)
        assert ok is False
        assert msg == "release is None, ignored"

    def test__is_gateway_ok_for_releasing_with_inactive_gateway(self, fake_gateway, fake_release):
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()
        source = PublishSourceEnum.BACKEND_UPDATE
        ok, msg = _is_gateway_ok_for_releasing(fake_release, source)
        assert ok is False
        assert "is not active, skip" in msg

    def test__is_gateway_ok_for_releasing_with_inactive_stage(self, fake_stage, fake_release):
        fake_stage.status = StageStatusEnum.INACTIVE.value
        fake_stage.save()
        source = PublishSourceEnum.BACKEND_UPDATE
        ok, msg = _is_gateway_ok_for_releasing(fake_release, source)
        assert ok is False
        assert f"stage(name={fake_stage.name}) is not active, ignored" in msg

    def test__is_gateway_ok_for_releasing_with_valid_release(self, fake_release):
        source = PublishSourceEnum.CLI_SYNC
        ok, msg = _is_gateway_ok_for_releasing(fake_release, source)
        assert ok is True
        assert msg == ""

    def test__save_release_history(self, fake_release):
        source = PublishSourceEnum.BACKEND_UPDATE
        release_history = _save_release_history(fake_release, source, "test")
        assert release_history is not None
        assert release_history.gateway.pk == fake_release.gateway_id
        assert release_history.stage.pk == fake_release.stage_id

    def test__trigger_rolling_publish(self, fake_shared_gateway, fake_release):
        fake_shared_gateway.id = settings.DEFAULT_MICRO_GATEWAY_ID
        fake_shared_gateway.save()
        source = PublishSourceEnum.BACKEND_UPDATE
        release_list = [fake_release]
        self.distributor.distribute.return_value = True, ""
        _trigger_rolling_publish(source, "test", release_list, True)
        self.distributor.distribute.assert_called()

    def test__trigger_revoke_publish_for_disable_with_valid_release(self, fake_shared_gateway, fake_release):
        fake_shared_gateway.id = settings.DEFAULT_MICRO_GATEWAY_ID
        fake_shared_gateway.save()
        source = PublishSourceEnum.GATEWAY_DISABLE
        release_list = [fake_release]
        self.distributor.revoke.return_value = True, ""
        _trigger_revoke_publish_for_disable(source, "test", release_list, True)
        self.distributor.revoke.assert_called()
