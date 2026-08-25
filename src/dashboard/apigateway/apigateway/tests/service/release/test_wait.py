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
from unittest.mock import patch

from ddf import G

from apigateway.core.constants import (
    PublishEventNameTypeEnum,
    PublishEventStatusTypeEnum,
    ReleaseHistoryStatusEnum,
    StageStatusEnum,
)
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, ResourceVersion
from apigateway.service.release import wait_release_done, wait_release_ready


class TestWaitReleaseDone:
    def test_success(self, fake_release_history):
        """发布成功时返回 SUCCESS"""
        G(
            PublishEvent,
            publish=fake_release_history,
            name=PublishEventNameTypeEnum.LOAD_CONFIGURATION.value,
            status=PublishEventStatusTypeEnum.SUCCESS.value,
        )

        with patch("apigateway.service.release.wait.time.sleep"):
            result = wait_release_done(fake_release_history.id)

        assert result == ReleaseHistoryStatusEnum.SUCCESS.value

    def test_failure(self, fake_release_history):
        """发布失败时返回 FAILURE"""
        G(
            PublishEvent,
            publish=fake_release_history,
            name=PublishEventNameTypeEnum.LOAD_CONFIGURATION.value,
            status=PublishEventStatusTypeEnum.FAILURE.value,
        )

        with patch("apigateway.service.release.wait.time.sleep"):
            result = wait_release_done(fake_release_history.id)

        assert result == ReleaseHistoryStatusEnum.FAILURE.value

    def test_timeout(self, fake_release_history):
        """超时返回 FAILURE"""
        with patch("apigateway.service.release.wait.time.sleep"):
            result = wait_release_done(fake_release_history.id, timeout=0)

        assert result == ReleaseHistoryStatusEnum.FAILURE.value


class TestWaitReleaseReady:
    def test_success_waits_for_matching_active_release(self, fake_release_history):
        fake_stage = fake_release_history.stage
        fake_stage.status = StageStatusEnum.INACTIVE.value
        fake_stage.save(update_fields=["status"])
        G(
            Release,
            gateway=fake_release_history.gateway,
            stage=fake_stage,
            resource_version=fake_release_history.resource_version,
        )

        def activate_stage(_seconds):
            type(fake_stage).objects.filter(id=fake_stage.id).update(status=StageStatusEnum.ACTIVE.value)

        with (
            patch(
                "apigateway.service.release.wait.wait_release_done",
                return_value=ReleaseHistoryStatusEnum.SUCCESS.value,
            ),
            patch("apigateway.service.release.wait.time.sleep", side_effect=activate_stage),
        ):
            result = wait_release_ready(fake_release_history.id)

        assert result == ReleaseHistoryStatusEnum.SUCCESS.value

    def test_success_waits_for_current_release_resource_version(self, fake_release_history):
        fake_stage = fake_release_history.stage
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save(update_fields=["status"])
        old_resource_version = G(
            ResourceVersion,
            gateway=fake_release_history.gateway,
            version="old-version",
            _data="[]",
        )
        release = G(
            Release,
            gateway=fake_release_history.gateway,
            stage=fake_stage,
            resource_version=old_resource_version,
        )

        def switch_release_version(_seconds):
            Release.objects.filter(id=release.id).update(resource_version_id=fake_release_history.resource_version_id)

        with (
            patch(
                "apigateway.service.release.wait.wait_release_done",
                return_value=ReleaseHistoryStatusEnum.SUCCESS.value,
            ),
            patch("apigateway.service.release.wait.time.sleep", side_effect=switch_release_version),
        ):
            result = wait_release_ready(fake_release_history.id)

        release.refresh_from_db()
        assert result == ReleaseHistoryStatusEnum.SUCCESS.value
        assert release.resource_version_id == fake_release_history.resource_version_id

    def test_failure_does_not_require_release_history(self):
        missing_release_history_id = 2_147_483_647

        with patch(
            "apigateway.service.release.wait.wait_release_done",
            return_value=ReleaseHistoryStatusEnum.FAILURE.value,
        ):
            result = wait_release_ready(missing_release_history_id)

        assert result == ReleaseHistoryStatusEnum.FAILURE.value

    def test_success_event_without_ready_release_times_out(self, fake_release_history):
        fake_stage = fake_release_history.stage
        fake_stage.status = StageStatusEnum.INACTIVE.value
        fake_stage.save(update_fields=["status"])
        G(
            Release,
            gateway=fake_release_history.gateway,
            stage=fake_stage,
            resource_version=fake_release_history.resource_version,
        )

        with patch(
            "apigateway.service.release.wait.wait_release_done",
            return_value=ReleaseHistoryStatusEnum.SUCCESS.value,
        ):
            result = wait_release_ready(fake_release_history.id, timeout=0)

        assert result == ReleaseHistoryStatusEnum.FAILURE.value

    def test_event_wait_consumes_total_timeout_budget(self, fake_release_history):
        fake_stage = fake_release_history.stage
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save(update_fields=["status"])
        G(
            Release,
            gateway=fake_release_history.gateway,
            stage=fake_stage,
            resource_version=fake_release_history.resource_version,
        )
        current_time = 0.0

        def finish_event_wait(_release_history_id, *, timeout):
            nonlocal current_time
            assert timeout == 150
            current_time = 150.0
            return ReleaseHistoryStatusEnum.SUCCESS.value

        with (
            patch("apigateway.service.release.wait.time.monotonic", side_effect=lambda: current_time),
            patch("apigateway.service.release.wait.wait_release_done", side_effect=finish_event_wait),
        ):
            result = wait_release_ready(fake_release_history.id)

        assert result == ReleaseHistoryStatusEnum.FAILURE.value

    def test_success_event_with_deleted_release_history_returns_failure(self, fake_release_history):
        release_history_id = fake_release_history.id

        def delete_release_history(_release_history_id, *, timeout):
            assert timeout == 150
            ReleaseHistory.objects.filter(id=release_history_id).delete()
            return ReleaseHistoryStatusEnum.SUCCESS.value

        with patch(
            "apigateway.service.release.wait.wait_release_done",
            side_effect=delete_release_history,
        ):
            result = wait_release_ready(release_history_id)

        assert result == ReleaseHistoryStatusEnum.FAILURE.value
