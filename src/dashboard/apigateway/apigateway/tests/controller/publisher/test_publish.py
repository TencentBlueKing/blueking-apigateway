#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from unittest.mock import Mock, patch

import pytest

from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.controller.publisher.publish import (
    _trigger_revoke_deleting,
    _trigger_revoke_disable,
    _trigger_rolling_update,
    trigger_gateway_publish,
)
from apigateway.core.constants import (
    PublishSourceEnum,
)
from apigateway.core.models import Gateway, Release, ReleaseHistory, ResourceVersion, Stage


class TestTriggerRollingUpdate:
    """Test _trigger_rolling_update function"""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway"""
        gateway = Mock(spec=Gateway)
        gateway.pk = 1
        return gateway

    @pytest.fixture
    def mock_stage(self):
        """Create a mock stage"""
        stage = Mock(spec=Stage)
        stage.pk = 1
        return stage

    @pytest.fixture
    def mock_resource_version(self):
        """Create a mock resource version"""
        resource_version = Mock(spec=ResourceVersion)
        resource_version.pk = 1
        return resource_version

    @pytest.fixture
    def mock_release(self, mock_gateway, mock_stage, mock_resource_version):
        """Create a mock release"""
        release = Mock(spec=Release)
        release.pk = 1
        release.gateway = mock_gateway
        release.gateway_id = 1
        release.stage = mock_stage
        release.resource_version = mock_resource_version
        return release

    @patch("apigateway.controller.publisher.publish.rolling_update_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    def test_trigger_rolling_update_success(
        self,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_rolling_update,
        mock_release,
    ):
        """Test successful rolling update"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_release_history.pk = 123
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (True, "")

        result = _trigger_rolling_update(
            PublishSourceEnum.GATEWAY_ENABLE,
            "test_user",
            [mock_release],
            is_sync=False,
        )

        assert result is True
        mock_save_history.assert_called_once()
        mock_check.assert_called_once()
        mock_reporter.report_config_validate_success.assert_called_once()
        mock_reporter.report_create_publish_task_doing.assert_called_once()

    @patch("apigateway.controller.publisher.publish.rolling_update_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    def test_trigger_rolling_update_cli_sync(
        self,
        mock_check,
        mock_reporter,
        mock_rolling_update,
        mock_release,
    ):
        """Test rolling update for CLI sync source"""
        mock_check.return_value = (True, "")

        result = _trigger_rolling_update(
            PublishSourceEnum.CLI_SYNC,
            "cli_user",
            [mock_release],
            is_sync=False,
        )

        assert result is True
        mock_check.assert_called_once()
        mock_reporter.report_config_validate_success.assert_called_once()
        mock_reporter.report_create_publish_task_doing.assert_called_once()

    @patch("apigateway.controller.publisher.publish.rolling_update_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    def test_trigger_rolling_update_check_failure(
        self,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_rolling_update,
        mock_release,
    ):
        """Test rolling update when check fails"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (False, "Gateway not ready")

        result = _trigger_rolling_update(
            PublishSourceEnum.GATEWAY_ENABLE,
            "test_user",
            [mock_release],
            is_sync=False,
        )

        assert result is True
        mock_reporter.report_config_validate_failure.assert_called_once()
        mock_rolling_update.assert_not_called()

    @patch("apigateway.controller.publisher.publish.rolling_update_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    def test_trigger_rolling_update_sync_mode(
        self,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_rolling_update,
        mock_release,
    ):
        """Test rolling update in sync mode"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_release_history.pk = 123
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (True, "")

        result = _trigger_rolling_update(
            PublishSourceEnum.GATEWAY_ENABLE,
            "test_user",
            [mock_release],
            is_sync=True,
        )

        assert result is True
        mock_rolling_update.assert_called_once_with(
            gateway_id=1,
            publish_id=123,
            release_id=1,
        )

    @patch("apigateway.controller.publisher.publish.delay_on_commit")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    def test_trigger_rolling_update_async_mode(
        self,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_delay_on_commit,
        mock_release,
    ):
        """Test rolling update in async mode"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_release_history.pk = 123
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (True, "")

        result = _trigger_rolling_update(
            PublishSourceEnum.GATEWAY_ENABLE,
            "test_user",
            [mock_release],
            is_sync=False,
        )

        assert result is True
        mock_delay_on_commit.assert_called_once()


class TestTriggerRevokeDisable:
    """Test _trigger_revoke_disable function"""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway"""
        gateway = Mock(spec=Gateway)
        gateway.pk = 1
        return gateway

    @pytest.fixture
    def mock_stage(self):
        """Create a mock stage"""
        stage = Mock(spec=Stage)
        stage.pk = 1
        return stage

    @pytest.fixture
    def mock_resource_version(self):
        """Create a mock resource version"""
        resource_version = Mock(spec=ResourceVersion)
        resource_version.pk = 1
        return resource_version

    @pytest.fixture
    def mock_release(self, mock_gateway, mock_stage, mock_resource_version):
        """Create a mock release"""
        release = Mock(spec=Release)
        release.pk = 1
        release.id = 1
        release.gateway = mock_gateway
        release.stage = mock_stage
        release.resource_version = mock_resource_version
        return release

    @pytest.fixture
    def mock_user_credentials(self):
        """Create a mock user credentials"""
        return Mock(spec=UserCredentials)

    @patch("apigateway.controller.publisher.publish.revoke_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    @patch("apigateway.controller.publisher.publish._pre_publish_programmable_gateway_offline")
    def test_trigger_revoke_disable_success(
        self,
        mock_offline,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_revoke_release,
        mock_release,
        mock_user_credentials,
    ):
        """Test successful revoke disable"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_release_history.id = 123
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (True, "")

        result = _trigger_revoke_disable(
            PublishSourceEnum.GATEWAY_DISABLE,
            "test_user",
            [mock_release],
            is_sync=False,
            user_credentials=mock_user_credentials,
        )

        assert result is None
        mock_save_history.assert_called_once()
        mock_offline.assert_called_once()
        mock_check.assert_called_once()
        mock_reporter.report_config_validate_success.assert_called_once()
        mock_reporter.report_create_publish_task_doing.assert_called_once()

    @patch("apigateway.controller.publisher.publish.revoke_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    @patch("apigateway.controller.publisher.publish._pre_publish_programmable_gateway_offline")
    def test_trigger_revoke_disable_check_failure(
        self,
        mock_offline,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_revoke_release,
        mock_release,
        mock_user_credentials,
    ):
        """Test revoke disable when check fails"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (False, "Gateway not ready")

        result = _trigger_revoke_disable(
            PublishSourceEnum.GATEWAY_DISABLE,
            "test_user",
            [mock_release],
            is_sync=False,
            user_credentials=mock_user_credentials,
        )

        assert result is None
        mock_reporter.report_config_validate_failure.assert_called_once()
        mock_revoke_release.assert_not_called()

    @patch("apigateway.controller.publisher.publish.revoke_release")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    @patch("apigateway.controller.publisher.publish._pre_publish_programmable_gateway_offline")
    def test_trigger_revoke_disable_sync_mode(
        self,
        mock_offline,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_revoke_release,
        mock_release,
        mock_user_credentials,
    ):
        """Test revoke disable in sync mode"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_release_history.id = 123
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (True, "")

        result = _trigger_revoke_disable(
            PublishSourceEnum.GATEWAY_DISABLE,
            "test_user",
            [mock_release],
            is_sync=True,
            user_credentials=mock_user_credentials,
        )

        assert result is not None  # In sync mode, returns result of revoke_release
        mock_revoke_release.assert_called_once_with(
            release_id=1,
            publish_id=123,
        )

    @patch("apigateway.controller.publisher.publish.delay_on_commit")
    @patch("apigateway.controller.publisher.publish.PublishEventReporter")
    @patch("apigateway.controller.publisher.publish._pre_publish_check_is_gateway_ready_for_releasing")
    @patch("apigateway.controller.publisher.publish._pre_publish_save_release_history")
    @patch("apigateway.controller.publisher.publish._pre_publish_programmable_gateway_offline")
    def test_trigger_revoke_disable_async_mode(
        self,
        mock_offline,
        mock_save_history,
        mock_check,
        mock_reporter,
        mock_delay_on_commit,
        mock_release,
        mock_user_credentials,
    ):
        """Test revoke disable in async mode"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_release_history.id = 123
        mock_save_history.return_value = mock_release_history
        mock_check.return_value = (True, "")

        result = _trigger_revoke_disable(
            PublishSourceEnum.GATEWAY_DISABLE,
            "test_user",
            [mock_release],
            is_sync=False,
            user_credentials=mock_user_credentials,
        )

        assert result is None
        mock_delay_on_commit.assert_called_once()


class TestTriggerRevokeDeleting:
    """Test _trigger_revoke_deleting function"""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway"""
        gateway = Mock(spec=Gateway)
        gateway.pk = 1
        return gateway

    @pytest.fixture
    def mock_stage(self):
        """Create a mock stage"""
        stage = Mock(spec=Stage)
        stage.pk = 1
        return stage

    @pytest.fixture
    def mock_resource_version(self):
        """Create a mock resource version"""
        resource_version = Mock(spec=ResourceVersion)
        resource_version.pk = 1
        return resource_version

    @pytest.fixture
    def mock_release(self, mock_gateway, mock_stage, mock_resource_version):
        """Create a mock release"""
        release = Mock(spec=Release)
        release.pk = 1
        release.id = 1
        release.gateway = mock_gateway
        release.stage = mock_stage
        release.resource_version = mock_resource_version
        return release

    @patch("apigateway.controller.publisher.publish.revoke_release")
    def test_trigger_revoke_deleting_sync_mode(self, mock_revoke_release, mock_release):
        """Test revoke deleting in sync mode"""
        result = _trigger_revoke_deleting([mock_release], is_sync=True)

        assert result is not None  # In sync mode, returns result of revoke_release
        mock_revoke_release.assert_called_once_with(
            release_id=1,
            publish_id=-2,  # DELETE_PUBLISH_ID
        )

    @patch("apigateway.controller.publisher.publish.delay_on_commit")
    def test_trigger_revoke_deleting_async_mode(self, mock_delay_on_commit, mock_release):
        """Test revoke deleting in async mode"""
        result = _trigger_revoke_deleting([mock_release], is_sync=False)

        assert result is None
        mock_delay_on_commit.assert_called_once()

    @patch("apigateway.controller.publisher.publish.revoke_release")
    def test_trigger_revoke_deleting_multiple_releases(self, mock_revoke_release):
        """Test revoke deleting with multiple releases"""
        release1 = Mock(spec=Release)
        release1.id = 1
        release2 = Mock(spec=Release)
        release2.id = 2

        result = _trigger_revoke_deleting([release1, release2], is_sync=True)

        assert result is not None  # Returns result from first revoke_release call
        assert mock_revoke_release.call_count == 1  # Only first one called (early return)


class TestTriggerGatewayPublish:
    """Test trigger_gateway_publish function"""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway"""
        gateway = Mock(spec=Gateway)
        gateway.pk = 1
        return gateway

    @pytest.fixture
    def mock_stage(self):
        """Create a mock stage"""
        stage = Mock(spec=Stage)
        stage.pk = 1
        return stage

    @pytest.fixture
    def mock_resource_version(self):
        """Create a mock resource version"""
        resource_version = Mock(spec=ResourceVersion)
        resource_version.pk = 1
        return resource_version

    @pytest.fixture
    def mock_release(self, mock_gateway, mock_stage, mock_resource_version):
        """Create a mock release"""
        release = Mock(spec=Release)
        release.pk = 1
        release.gateway = mock_gateway
        release.stage = mock_stage
        release.resource_version = mock_resource_version
        return release

    @pytest.fixture
    def mock_user_credentials(self):
        """Create a mock user credentials"""
        return Mock(spec=UserCredentials)

    @patch("apigateway.controller.publisher.publish.Release.objects.filter")
    def test_trigger_gateway_publish_no_releases(self, mock_filter):
        """Test when no releases exist"""
        mock_filter.return_value.prefetch_related.return_value.all.return_value = []

        result = trigger_gateway_publish(
            PublishSourceEnum.GATEWAY_ENABLE,
            "test_user",
            gateway_id=1,
        )

        assert result is True

    @patch("apigateway.controller.publisher.publish._trigger_rolling_update")
    @patch("apigateway.controller.publisher.publish.Release.objects.filter")
    def test_trigger_gateway_publish_rolling_update(
        self,
        mock_filter,
        mock_trigger_rolling_update,
        mock_release,
    ):
        """Test rolling update trigger"""
        mock_filter.return_value.prefetch_related.return_value.all.return_value = [mock_release]
        mock_trigger_rolling_update.return_value = True

        result = trigger_gateway_publish(
            PublishSourceEnum.GATEWAY_ENABLE,
            "test_user",
            gateway_id=1,
        )

        assert result is True
        mock_trigger_rolling_update.assert_called_once()

    @patch("apigateway.controller.publisher.publish._trigger_revoke_disable")
    @patch("apigateway.controller.publisher.publish.Release.objects.filter")
    def test_trigger_gateway_publish_revoke_disable(
        self,
        mock_filter,
        mock_trigger_revoke_disable,
        mock_release,
        mock_user_credentials,
    ):
        """Test revoke disable trigger"""
        mock_filter.return_value.prefetch_related.return_value.all.return_value = [mock_release]
        mock_trigger_revoke_disable.return_value = None

        result = trigger_gateway_publish(
            PublishSourceEnum.GATEWAY_DISABLE,
            "test_user",
            gateway_id=1,
            user_credentials=mock_user_credentials,
        )

        assert result is None
        mock_trigger_revoke_disable.assert_called_once()

    @patch("apigateway.controller.publisher.publish._trigger_revoke_deleting")
    @patch("apigateway.controller.publisher.publish.Release.objects.filter")
    def test_trigger_gateway_publish_revoke_deleting(
        self,
        mock_filter,
        mock_trigger_revoke_deleting,
        mock_release,
    ):
        """Test revoke deleting trigger"""
        mock_filter.return_value.prefetch_related.return_value.all.return_value = [mock_release]
        mock_trigger_revoke_deleting.return_value = None

        result = trigger_gateway_publish(
            PublishSourceEnum.STAGE_DELETE,
            "test_user",
            gateway_id=1,
        )

        assert result is None
        mock_trigger_revoke_deleting.assert_called_once()

    @patch("apigateway.controller.publisher.publish.Release.objects.filter")
    def test_trigger_gateway_publish_with_stage_id(self, mock_filter, mock_release):
        """Test with specific stage_id"""
        mock_filter.return_value.filter.return_value.prefetch_related.return_value.all.return_value = [mock_release]

        with patch("apigateway.controller.publisher.publish._trigger_rolling_update") as mock_trigger:
            mock_trigger.return_value = True

            result = trigger_gateway_publish(
                PublishSourceEnum.GATEWAY_ENABLE,
                "test_user",
                gateway_id=1,
                stage_id=123,
            )

            assert result is True
            mock_filter.assert_called_once_with(gateway_id=1)
            mock_filter.return_value.filter.assert_called_once_with(stage_id=123)
