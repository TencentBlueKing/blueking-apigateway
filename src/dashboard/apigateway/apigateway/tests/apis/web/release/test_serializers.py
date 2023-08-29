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
from apigateway.apis.web.release.serializers import PublishEventQueryOutputSLZ, ReleaseHistoryOutputSLZ
from apigateway.biz.release import ReleaseHandler
from apigateway.core.constants import PublishEventNameTypeEnum, PublishEventStatusTypeEnum
from apigateway.core.models import Gateway, PublishEvent, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import create_gateway, create_request, dummy_time


class TestReleaseBatchInputSLZ:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = G(Gateway)
        self.request = create_request()
        self.request.gateway = self.gateway

    def test_validate_stage_ids(self, mocker):
        stage_1 = G(Stage, api=self.gateway)
        stage_2 = G(Stage, api=self.gateway)

        gateway = G(Gateway)
        stage_3 = G(Stage, api=gateway)

        resource_version = G(ResourceVersion, gateway=self.gateway)

        data = [
            {
                "stage_ids": [stage_1.id, stage_2.id],
                "resource_version_id": resource_version.id,
                "expected": {
                    "gateway": self.gateway,
                    "stage_ids": [stage_1.id, stage_2.id],
                    "resource_version_id": resource_version.id,
                },
            },
            # error, stage_3 not belong to api
            {
                "stage_ids": [stage_3.id, stage_1.id],
                "resource_version_id": resource_version.id,
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.ReleaseBatchInputSLZ(data=test, context={"api": self.gateway})
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

        stage = G(Stage, api=self.gateway)
        resource_version_2 = G(ResourceVersion, gateway=self.gateway)

        data = [
            # ok
            {
                "stage_ids": [stage.id],
                "resource_version_id": resource_version_2.id,
                "expected": {
                    "gateway": self.gateway,
                    "stage_ids": [stage.id],
                    "resource_version_id": resource_version_2.id,
                },
            },
            # error, resoruce_version not belong to self.gateway
            {
                "stage_ids": [stage.id],
                "resource_version_id": resource_version_1.id,
                "will_error": True,
            },
        ]
        for test in data:
            slz = serializers.ReleaseBatchInputSLZ(data=test, context={"api": self.gateway})
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
        stage = G(Stage, api=gateway)
        resource_version = G(ResourceVersion, gateway=gateway, name="t1", version="1.0.0", title="测试", comment="test1")
        release_history = G(
            ReleaseHistory,
            gateway=gateway,
            stage=stage,
            source="test",
            resource_version=resource_version,
            created_time=dummy_time.time,
        )
        release_history.stages.add(stage)
        event_1 = G(
            PublishEvent,
            publish=release_history,
            name=PublishEventNameTypeEnum.ValidateConfiguration.value,
            status=PublishEventStatusTypeEnum.FAILURE.value,
            created_time=dummy_time.time + datetime.timedelta(seconds=10),
        )

        slz = ReleaseHistoryOutputSLZ(
            release_history,
            context={
                "publish_events_map": ReleaseHandler.get_latest_publish_event_by_release_history_ids(
                    [release_history.id]
                ),
            },
        )
        assert slz.data == {
            "publish_id": release_history.id,
            "stage_names": [stage.name],
            "created_time": dummy_time.str,
            "created_by": release_history.created_by,
            "resource_version_display": "1.0.0(测试)",
            "status": f"{event_1.name} {event_1.status}",
            "source": release_history.source,
            "cost": (event_1.created_time - release_history.created_time).total_seconds(),
            "is_running": False,
        }


class TestPublishEventQueryOutputSLZ:
    def test_to_representation(self, fake_stage, fake_release_history, fake_publish_event):
        fake_release_history.stages.add(fake_stage)
        slz = PublishEventQueryOutputSLZ(
            fake_release_history,
            context={
                "publish_events_map": ReleaseHandler.get_latest_publish_event_by_release_history_ids(
                    [fake_release_history.id]
                ),
                "publish_events": ReleaseHandler.get_publish_events_by_release_history_id(fake_release_history.id),
            },
        )
        assert slz.data == {
            "publish_id": fake_release_history.id,
            "stage_names": [fake_stage.name],
            "resource_version_display": fake_release_history.resource_version.object_display,
            "created_time": dummy_time.str,
            "created_by": fake_release_history.created_by,
            "source": fake_release_history.source,
            "cost": 0,
            "status": f"{fake_publish_event.name} {fake_publish_event.status}",
            "is_running": True,
            "events": [
                {
                    "event_id": fake_publish_event.id,
                    "publish_id": fake_release_history.id,
                    "name": fake_publish_event.name,
                    "step": fake_publish_event.step,
                    "status": fake_publish_event.status,
                    "created_time": dummy_time.str,
                    "msg": "{}",
                }
            ],
        }
