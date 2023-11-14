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
import datetime

import pytest
from dateutil.tz import tzutc
from django.http import Http404
from django_dynamic_fixture import G

from apigateway.apis.web.release import serializers
from apigateway.apis.web.release.serializers import ReleaseHistoryEventRetrieveOutputSLZ, ReleaseHistoryOutputSLZ
from apigateway.biz.release import ReleaseHandler
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusEnum, PublishEventStatusTypeEnum
from apigateway.core.models import Gateway, PublishEvent, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, create_request, dummy_time


class TestReleaseInputSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway

    def test_validate_stage_id(self, mocker):
        stage_1 = G(Stage, gateway=self.gateway)

        gateway = G(Gateway)
        stage_3 = G(Stage, gateway=gateway)

        resource_version = G(ResourceVersion, gateway=self.gateway)

        data = [
            {
                "stage_id": stage_1.id,
                "resource_version_id": resource_version.id,
                "expected": {
                    "gateway": self.gateway,
                    "stage_id": stage_1.id,
                    "resource_version_id": resource_version.id,
                },
            },
            # error, stage_3 not belong to gateway
            {
                "stage_id": stage_3.id,
                "resource_version_id": resource_version.id,
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.ReleaseInputSLZ(data=test, context={"gateway": self.gateway})
            if test.get("will_error"):
                with pytest.raises(Http404):
                    slz.is_valid()
            else:
                slz.is_valid()
                assert not slz.errors
                assert slz.validated_data == test["expected"]

    def test_validate_resource_version_id(self, mocker):
        gateway = create_gateway()
        resource_version_1 = G(ResourceVersion, gateway=gateway)

        stage = G(Stage, gateway=self.gateway)
        resource_version_2 = G(ResourceVersion, gateway=self.gateway)

        data = [
            # ok
            {
                "stage_id": stage.id,
                "resource_version_id": resource_version_2.id,
                "expected": {
                    "gateway": self.gateway,
                    "stage_id": stage.id,
                    "resource_version_id": resource_version_2.id,
                },
            },
            # error, resoruce_version not belong to self.gateway
            {
                "stage_id": [stage.id],
                "resource_version_id": resource_version_1.id,
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.ReleaseInputSLZ(data=test, context={"gateway": self.gateway})
            if test.get("will_error"):
                with pytest.raises(Http404):
                    slz.is_valid()
            else:
                slz.is_valid()
                assert not slz.errors
                assert slz.validated_data == test["expected"]


class TestReleaseHistoryQueryInputSLZ:
    def test_to_internal_value(self):
        data = [
            {
                "query": "test",
                "stage_id": 12345,
                "created_by": "admin",
                "time_start": 1577263732,
                "time_end": 1577263732,
                "expected": {
                    "query": "test",
                    "stage_id": 12345,
                    "created_by": "admin",
                    "time_start": datetime.datetime(2019, 12, 25, 8, 48, 52, tzinfo=tzutc()),
                    "time_end": datetime.datetime(2019, 12, 25, 8, 48, 52, tzinfo=tzutc()),
                },
            },
            {
                "query": "test",
                "stage_id": 12345,
                "created_by": "admin",
                "time_start": None,
                "time_end": None,
                "expected": {
                    "query": "test",
                    "stage_id": 12345,
                    "created_by": "admin",
                    "time_start": None,
                    "time_end": None,
                },
            },
        ]

        for test in data:
            slz = serializers.ReleaseHistoryQueryInputSLZ(data=test)
            slz.is_valid()
            assert not slz.errors
            assert slz.validated_data == test["expected"]


class TestReleaseHistoryOutputSLZ:
    def test_to_representation(self):
        gateway = G(Gateway)
        stage = G(Stage, gateway=gateway)
        resource_version = G(
            ResourceVersion, gateway=gateway, name="t1", version="1.0.0", title="测试", comment="test1"
        )
        release_history = G(
            ReleaseHistory,
            gateway=gateway,
            stage=stage,
            source="test",
            resource_version=resource_version,
            created_time=dummy_time.time,
        )
        event_1 = G(
            PublishEvent,
            publish=release_history,
            name=PublishEventNameTypeEnum.VALIDATE_CONFIGURATION.value,
            status=PublishEventStatusTypeEnum.FAILURE.value,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
        )

        slz = ReleaseHistoryOutputSLZ(
            release_history,
            context={
                "release_history_events_map": ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
                    [release_history.id]
                ),
            },
        )
        assert slz.data == {
            "id": release_history.id,
            "stage": {"id": stage.id, "name": stage.name},
            "created_time": dummy_time.str,
            "created_by": release_history.created_by,
            "resource_version_display": "1.0.0",
            "status": f"{event_1.status}",
            "source": release_history.source,
            "duration": (event_1.created_time - release_history.created_time).total_seconds(),
        }


class TestPublishEventQueryOutputSLZ:
    def test_to_representation(self, fake_stage, fake_release_history, fake_publish_event):
        slz = ReleaseHistoryEventRetrieveOutputSLZ(
            fake_release_history,
            context={
                "release_history_events_map": ReleaseHandler.get_release_history_id_to_latest_publish_event_map(
                    [fake_release_history.id]
                ),
                "release_history_events": ReleaseHandler.list_publish_events_by_release_history_id(
                    fake_release_history.id
                ),
            },
        )
        assert slz.data == {
            "id": fake_release_history.id,
            "stage": {"id": fake_stage.id, "name": fake_stage.name},
            "resource_version_display": fake_release_history.resource_version.object_display,
            "created_time": dummy_time.str,
            "created_by": fake_release_history.created_by,
            "source": fake_release_history.source,
            "status": PublishEventStatusEnum.FAILURE.value,
            "duration": 0,
            "events": [
                {
                    "id": fake_publish_event.id,
                    "release_history_id": fake_release_history.id,
                    "name": fake_publish_event.name,
                    "step": fake_publish_event.step,
                    "status": fake_publish_event.status,
                    "created_time": dummy_time.str,
                    "detail": {},
                },
                {
                    "id": -fake_publish_event.step,
                    "release_history_id": fake_release_history.id,
                    "name": fake_publish_event.name,
                    "step": fake_publish_event.step,
                    "status": PublishEventStatusTypeEnum.FAILURE.value,
                    "created_time": dummy_time.str,
                    "detail": {},
                },
            ],
            "events_template": [
                {"name": "validata_configuration", "desc": "配置校验", "step": 0},
                {"name": "generate_release_task", "desc": "生成发布任务", "step": 1},
                {"name": "distribute_configuration", "desc": "下发配置", "step": 2},
                {"name": "parse_configuration", "desc": "解析配置", "step": 3},
                {"name": "apply_configuration", "desc": "应用配置", "step": 4},
                {"name": "load_configuration", "desc": "加载配置", "step": 5},
            ],
        }
