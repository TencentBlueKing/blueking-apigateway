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
import datetime
from unittest.mock import call

import pytest
from ddf import G

import apigateway.biz.release as release_biz
from apigateway.biz.release import ReleaseHandler
from apigateway.biz.release.gateway_releaser import ReleaseError, release_gateway
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusTypeEnum,
    StageStatusEnum,
)
from apigateway.core.models import Gateway, PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.tests.utils.testing import dummy_time
from apigateway.utils.time import now_datetime

pytestmark = pytest.mark.django_db


class TestReleaseHandler:
    def test_package_release_gateway_export_is_callable(self):
        assert release_biz.release_gateway is release_gateway
        assert callable(release_biz.release_gateway)

    def test_filter_release_history(self):
        gateway = G(Gateway)
        stage_prod = G(Stage, gateway=gateway, name="prod")
        stage_test = G(Stage, gateway=gateway, name="test")
        resource_version_1 = G(ResourceVersion, gateway=gateway)
        resource_version_2 = G(ResourceVersion, gateway=gateway)

        G(ReleaseHistory, gateway=gateway, stage=stage_prod, resource_version=resource_version_1)
        G(ReleaseHistory, gateway=gateway, stage=stage_prod, resource_version=resource_version_1, created_by="admin")
        G(
            ReleaseHistory,
            gateway=gateway,
            stage=stage_prod,
            resource_version=resource_version_1,
            created_time=dummy_time.time,
        )
        G(ReleaseHistory, gateway=gateway, stage=stage_test, resource_version=resource_version_2)

        data = [
            {
                "params": {
                    "query": "prod",
                },
                "expected": {
                    "count": 3,
                },
            },
            {
                "params": {
                    "stage_id": stage_prod.id,
                },
                "expected": {
                    "count": 3,
                },
            },
            {
                "params": {
                    "created_by": "adm",
                },
                "expected": {
                    "count": 1,
                },
            },
            {
                "params": {
                    "time_start": dummy_time.time - datetime.timedelta(hours=1),
                    "time_end": dummy_time.time + datetime.timedelta(hours=1),
                },
                "expected": {
                    "count": 1,
                },
            },
        ]
        for test in data:
            result = ReleaseHandler.filter_release_history(gateway, fuzzy=True, **test["params"])
            assert result.count() == test["expected"]["count"]

    def test_filter_release_history_selects_data_plane(
        self, django_assert_num_queries, fake_gateway, default_data_plane
    ):
        stage = G(Stage, gateway=fake_gateway)
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        for _ in range(3):
            G(
                ReleaseHistory,
                gateway=fake_gateway,
                stage=stage,
                resource_version=resource_version,
                data_plane=default_data_plane,
            )

        queryset = ReleaseHandler.filter_release_history(fake_gateway, order_by="id")

        with django_assert_num_queries(1):
            data_plane_names = [history.data_plane.name for history in queryset]

        assert data_plane_names == [default_data_plane.name] * 3

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

    def test_release_to_stages_calls_release_once_per_stage(self, fake_gateway, mocker):
        stage_ids = [101, 102]
        resource_version_id = 201
        mocker.patch("apigateway.biz.release.release_handler.Lock")
        mocked_release_gateway = mocker.patch("apigateway.biz.release.release_handler.release_gateway")

        ok, message = ReleaseHandler.release_to_stages(
            gateway=fake_gateway,
            resource_version_id=resource_version_id,
            stage_ids=stage_ids,
            username="admin",
            comment="release",
        )

        assert ok is True
        assert message == ""
        mocked_release_gateway.assert_has_calls(
            [
                call(
                    gateway=fake_gateway,
                    stage_id=stage_ids[0],
                    resource_version_id=resource_version_id,
                    username="admin",
                    comment="release",
                ),
                call(
                    gateway=fake_gateway,
                    stage_id=stage_ids[1],
                    resource_version_id=resource_version_id,
                    username="admin",
                    comment="release",
                ),
            ]
        )

    def test_release_to_stages_returns_error_message(self, fake_gateway, mocker):
        mocker.patch("apigateway.biz.release.release_handler.Lock")
        mocker.patch(
            "apigateway.biz.release.release_handler.release_gateway",
            side_effect=ReleaseError("release failed"),
        )

        ok, message = ReleaseHandler.release_to_stages(
            gateway=fake_gateway,
            resource_version_id=201,
            stage_ids=[101],
            username="admin",
            comment="release",
        )

        assert ok is False
        assert message == "release failed"

    def test_release_to_stages_returns_error_after_partial_success(self, fake_gateway, mocker):
        mocker.patch("apigateway.biz.release.release_handler.Lock")
        mocked_release_gateway = mocker.patch(
            "apigateway.biz.release.release_handler.release_gateway",
            side_effect=[None, ReleaseError("release failed")],
        )

        ok, message = ReleaseHandler.release_to_stages(
            gateway=fake_gateway,
            resource_version_id=201,
            stage_ids=[101, 102],
            username="admin",
            comment="release",
        )

        assert ok is False
        assert message == "release failed"
        assert mocked_release_gateway.call_count == 2

    def test_get_latest_publish_event_by_release_history_ids(self, fake_release_history, fake_publish_event):
        assert (
            PublishEvent.objects.get_release_history_id_to_latest_publish_event_map([fake_release_history.id])[
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
            PublishEvent.objects.get_release_history_id_to_latest_publish_event_map([fake_release_history.id])[
                fake_release_history.id
            ]
            == event_2
        )

    def test_batch_get_stage_release_status(self, fake_stage, fake_release_history, fake_publish_event):
        assert (
            ReleaseHandler.batch_get_stage_release_status([fake_stage.id])[fake_stage.id]["status"]
            == PublishEventStatusTypeEnum.FAILURE.value
        )

        fake_publish_event.status = PublishEventStatusTypeEnum.FAILURE.value
        fake_publish_event.created_time = now_datetime()
        fake_publish_event.save()

        assert (
            ReleaseHandler.batch_get_stage_release_status([fake_stage.id])[fake_stage.id]["status"]
            == PublishEventStatusTypeEnum.FAILURE.value
        )

        fake_publish_event.status = PublishEventStatusTypeEnum.SUCCESS.value
        fake_publish_event.created_time = now_datetime()
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

    def test_batch_get_stage_release_status_uses_constant_queries(self, django_assert_num_queries, fake_gateway):
        stage_ids = []
        for index in range(3):
            stage = G(Stage, gateway=fake_gateway, name=f"stage-{index}")
            resource_version = G(ResourceVersion, gateway=fake_gateway, version=f"1.0.{index}")
            G(ReleaseHistory, gateway=fake_gateway, stage=stage, resource_version=resource_version)
            stage_ids.append(stage.id)

        with django_assert_num_queries(2):
            result = ReleaseHandler.batch_get_stage_release_status(stage_ids)

        assert set(result) == set(stage_ids)

    def test_batch_get_stage_release_status_uses_latest_release_history(self, fake_gateway):
        stage = G(Stage, gateway=fake_gateway)
        old_resource_version = G(ResourceVersion, gateway=fake_gateway, version="1.0.0")
        latest_resource_version = G(ResourceVersion, gateway=fake_gateway, version="2.0.0")
        G(ReleaseHistory, gateway=fake_gateway, stage=stage, resource_version=old_resource_version)
        latest_release_history = G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=stage,
            resource_version=latest_resource_version,
        )

        result = ReleaseHandler.batch_get_stage_release_status([stage.id])[stage.id]

        assert result["publish_id"] == latest_release_history.id
        assert result["resource_version_id"] == latest_resource_version.id
        assert result["resource_version_display"] == latest_resource_version.object_display
