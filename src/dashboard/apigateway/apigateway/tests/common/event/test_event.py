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
from apigateway.common.event.event import PublishEventReporter
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum
from apigateway.core.models import PublishEvent


class TestPublishEventReporter:
    def test_report_config_validate_doing_event(self, fake_release_history):
        PublishEventReporter.report_config_validate_doing_event(fake_release_history)
        assert PublishEvent.objects.filter(publish_id=fake_release_history.id).first()

    def test_report_config_validate_success_event(self, fake_release_history):
        PublishEventReporter.report_config_validate_success_event(fake_release_history)
        event = PublishEvent.objects.filter(publish_id=fake_release_history.id).first()
        assert event

    def test_report_config_validate_fail_event(self, fake_release_history):
        msg = "test_error_message"
        PublishEventReporter.report_config_validate_fail_event(fake_release_history, msg)
        event = PublishEvent.objects.filter(publish_id=fake_release_history.id).first()
        assert event

    def test_report_create_publish_task_doing_event(self, fake_release_history):
        PublishEventReporter.report_create_publish_task_doing_event(fake_release_history)

    def test_report_create_publish_task_success_event(self, fake_release_history):
        PublishEventReporter.report_create_publish_task_success_event(fake_release_history)
        result = PublishEvent.objects.filter(publish_id=fake_release_history.id).first()
        assert result is not None
        assert result.name == PublishEventNameTypeEnum.GENERATE_TASK.value
        assert result.status == PublishEventStatusTypeEnum.SUCCESS.value

    def test_report_distribute_configuration_doing_event(self, fake_release_history):
        PublishEventReporter.report_distribute_configuration_doing_event(fake_release_history)
        result = PublishEvent.objects.filter(publish_id=fake_release_history.id).first()
        assert result is not None
        assert result.name == PublishEventNameTypeEnum.DISTRIBUTE_CONFIGURATION.value
        assert result.status == PublishEventStatusTypeEnum.DOING.value

    def test_report_distribute_configuration_success_event(self, fake_release_history):
        PublishEventReporter.report_distribute_configuration_success_event(fake_release_history)
        result = PublishEvent.objects.filter(publish_id=fake_release_history.id).first()
        assert result is not None
        assert result.name == PublishEventNameTypeEnum.DISTRIBUTE_CONFIGURATION.value
        assert result.status == PublishEventStatusTypeEnum.SUCCESS.value

    def test_report_distribute_configuration_failure_event(self, fake_release_history):
        msg = "test_error_message"
        PublishEventReporter.report_distribute_configuration_failure_event(fake_release_history, msg)
        result = PublishEvent.objects.filter(publish_id=fake_release_history.id).first()
        assert result is not None
        assert result.name == PublishEventNameTypeEnum.DISTRIBUTE_CONFIGURATION.value
        assert result.status == PublishEventStatusTypeEnum.FAILURE.value
        assert result.detail == {"err_msg": msg}
