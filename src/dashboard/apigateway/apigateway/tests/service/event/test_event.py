#  -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
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

from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import PublishEvent
from apigateway.service.event import PublishEventReporter


@pytest.mark.parametrize(
    "reporter, name, status, step, detail",
    [
        ("report_config_validate_success", "validata_configuration", "success", 0, None),
        ("report_config_validate_failure", "validata_configuration", "failure", 0, {"err_msg": "invalid config"}),
        ("report_create_publish_task_doing", "generate_release_task", "doing", 1, None),
        ("report_create_publish_task_success", "generate_release_task", "success", 1, None),
        ("report_distribute_config_doing", "distribute_configuration", "doing", 2, None),
        ("report_distribute_config_success", "distribute_configuration", "success", 2, None),
        ("report_distribute_config_failure", "distribute_configuration", "failure", 2, {"err_msg": "sync failed"}),
    ],
)
class TestPublishEventReporter:
    def test_persists_event(self, fake_release_history, reporter, name, status, step, detail):
        args = [detail["err_msg"]] if detail else []
        previous_ids = set(PublishEvent.objects.values_list("id", flat=True))
        getattr(PublishEventReporter, reporter)(fake_release_history, *args)
        event = PublishEvent.objects.exclude(id__in=previous_ids).get()
        assert event.publish_id == fake_release_history.id
        assert event.gateway_id == fake_release_history.gateway_id
        assert event.stage_id == fake_release_history.stage_id
        assert (event.name, event.status, event.step, event.detail) == (name, status, step, detail)

    @pytest.mark.parametrize("publish_source", [None, PublishSourceEnum.CLI_SYNC.value])
    def test_suppresses_event(self, fake_release_history, reporter, name, status, step, detail, publish_source):
        publish = None
        if publish_source is not None:
            fake_release_history.source = publish_source
            publish = fake_release_history
        args = [detail["err_msg"]] if detail else []
        previous_ids = set(PublishEvent.objects.values_list("id", flat=True))
        getattr(PublishEventReporter, reporter)(publish, *args)
        assert set(PublishEvent.objects.values_list("id", flat=True)) == previous_ids
