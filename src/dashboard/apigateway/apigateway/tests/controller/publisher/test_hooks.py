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
from apigateway.controller.publisher.hooks import (
    _pre_publish_check_is_gateway_ready_for_releasing,
    _pre_publish_programmable_gateway_offline,
    _pre_publish_save_release_history,
)
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishSourceEnum,
    StageStatusEnum,
)
from apigateway.core.models import Gateway, Release, ReleaseHistory, ResourceVersion, Stage


class TestPrePublishCheckIsGatewayReadyForReleasing:
    """Test _pre_publish_check_is_gateway_ready_for_releasing function"""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway"""
        gateway = Mock(spec=Gateway)
        gateway.pk = 1
        gateway.status = GatewayStatusEnum.ACTIVE.value
        return gateway

    @pytest.fixture
    def mock_stage(self):
        """Create a mock stage"""
        stage = Mock(spec=Stage)
        stage.name = "prod"
        stage.status = StageStatusEnum.ACTIVE.value
        return stage

    @pytest.fixture
    def mock_resource_version(self):
        """Create a mock resource version"""
        resource_version = Mock(spec=ResourceVersion)
        resource_version.is_schema_v2 = True
        resource_version.object_display = "v1.0.0"
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

    def test_release_is_none(self):
        """Test when release is None"""
        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(None, PublishSourceEnum.GATEWAY_ENABLE)
        assert not ok
        assert msg == "release is None, ignored"

    def test_release_has_no_stage(self, mock_gateway, mock_resource_version):
        """Test when release has no stage"""
        release = Mock(spec=Release)
        release.pk = 1
        release.gateway = mock_gateway
        release.stage = None
        release.resource_version = mock_resource_version

        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(release, PublishSourceEnum.GATEWAY_ENABLE)
        assert not ok
        assert "has no stage" in msg

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_gateway_not_active(self, mock_gateway_get, mock_release):
        """Test when gateway is not active"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.INACTIVE.value

        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.STAGE_UPDATE)
        assert not ok
        assert "is not active" in msg

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_stage_not_active(self, mock_gateway_get, mock_release):
        """Test when stage is not active"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.ACTIVE.value
        mock_release.stage.status = StageStatusEnum.INACTIVE.value

        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.STAGE_UPDATE)
        assert not ok
        assert "stage" in msg and "is not active" in msg

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_resource_version_not_v2(self, mock_gateway_get, mock_release):
        """Test when resource version is not v2"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.ACTIVE.value
        mock_release.resource_version.is_schema_v2 = False

        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.STAGE_UPDATE)
        assert not ok
        assert "incompatible" in msg and "not allowed to be published" in msg

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_success_normal_publish(self, mock_gateway_get, mock_release):
        """Test successful normal publish"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.ACTIVE.value

        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.GATEWAY_ENABLE)
        assert ok
        assert msg == ""

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_gateway_enable_source_bypasses_status_check(self, mock_gateway_get, mock_release):
        """Test that GATEWAY_ENABLE source bypasses status checks"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.INACTIVE.value
        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.GATEWAY_ENABLE)
        assert ok
        assert msg == ""

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_revoke_disable_source_bypasses_status_check(self, mock_gateway_get, mock_release):
        """Test that TRIGGER_REVOKE_DISABLE_RELEASE bypasses status checks"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.INACTIVE.value
        mock_release.stage.status = StageStatusEnum.INACTIVE.value
        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.GATEWAY_DISABLE)
        assert ok
        assert msg == ""

    @patch("apigateway.controller.publisher.hooks.Gateway.objects.get")
    def test_revoke_disable_source_bypasses_version_check(self, mock_gateway_get, mock_release):
        """Test that TRIGGER_REVOKE_DISABLE_RELEASE bypasses version check"""
        mock_gateway_get.return_value.status = GatewayStatusEnum.ACTIVE.value
        mock_release.resource_version.is_schema_v2 = False

        ok, msg = _pre_publish_check_is_gateway_ready_for_releasing(mock_release, PublishSourceEnum.GATEWAY_DISABLE)
        assert ok
        assert msg == ""


class TestPrePublishSaveReleaseHistory:
    """Test _pre_publish_save_release_history function"""

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
        release.gateway = mock_gateway
        release.stage = mock_stage
        release.resource_version = mock_resource_version
        return release

    @patch("apigateway.controller.publisher.hooks.ReleaseHistory.objects.create")
    def test_save_release_history_success(self, mock_create, mock_release):
        """Test successful release history creation"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_create.return_value = mock_release_history

        result = _pre_publish_save_release_history(mock_release, PublishSourceEnum.GATEWAY_ENABLE, "test_user")

        mock_create.assert_called_once_with(
            gateway=mock_release.gateway,
            stage=mock_release.stage,
            source=PublishSourceEnum.GATEWAY_ENABLE.value,
            resource_version=mock_release.resource_version,
            created_by="test_user",
        )
        assert result == mock_release_history

    @patch("apigateway.controller.publisher.hooks.ReleaseHistory.objects.create")
    def test_save_release_history_with_different_source(self, mock_create, mock_release):
        """Test release history creation with different source"""
        mock_release_history = Mock(spec=ReleaseHistory)
        mock_create.return_value = mock_release_history

        result = _pre_publish_save_release_history(mock_release, PublishSourceEnum.CLI_SYNC, "cli_user")

        mock_create.assert_called_once_with(
            gateway=mock_release.gateway,
            stage=mock_release.stage,
            source=PublishSourceEnum.CLI_SYNC.value,
            resource_version=mock_release.resource_version,
            created_by="cli_user",
        )
        assert result == mock_release_history


class TestPrePublishProgrammableGatewayOffline:
    """Test _pre_publish_programmable_gateway_offline function"""

    @pytest.fixture
    def mock_gateway(self):
        """Create a mock gateway"""
        gateway = Mock(spec=Gateway)
        gateway.pk = 1
        gateway.name = "test-gateway"
        gateway.is_programmable = True
        return gateway

    @pytest.fixture
    def mock_stage(self):
        """Create a mock stage"""
        stage = Mock(spec=Stage)
        stage.name = "prod"
        return stage

    @pytest.fixture
    def mock_resource_version(self):
        """Create a mock resource version"""
        resource_version = Mock(spec=ResourceVersion)
        resource_version.version = "v1.0.0"
        return resource_version

    @pytest.fixture
    def mock_release(self, mock_gateway, mock_stage, mock_resource_version):
        """Create a mock release"""
        release = Mock(spec=Release)
        release.gateway = mock_gateway
        release.stage = mock_stage
        release.resource_version = mock_resource_version
        return release

    @pytest.fixture
    def mock_release_history(self):
        """Create a mock release history"""
        release_history = Mock(spec=ReleaseHistory)
        release_history.id = 123
        return release_history

    @pytest.fixture
    def mock_user_credentials(self):
        """Create a mock user credentials"""
        return Mock(spec=UserCredentials)

    def test_non_programmable_gateway(self, mock_release, mock_release_history, mock_user_credentials):
        """Test that non-programmable gateway is skipped"""
        mock_release.gateway.is_programmable = False

        with patch("apigateway.controller.publisher.hooks.paas_app_module_offline") as mock_offline:
            _pre_publish_programmable_gateway_offline(
                PublishSourceEnum.GATEWAY_DISABLE,
                "test_user",
                mock_release,
                mock_release_history,
                mock_user_credentials,
            )
            mock_offline.assert_not_called()

    def test_no_user_credentials(self, mock_release, mock_release_history):
        """Test that missing user credentials is skipped"""
        with patch("apigateway.controller.publisher.hooks.paas_app_module_offline") as mock_offline:
            _pre_publish_programmable_gateway_offline(
                PublishSourceEnum.GATEWAY_DISABLE,
                "test_user",
                mock_release,
                mock_release_history,
                None,
            )
            mock_offline.assert_not_called()

    @patch("apigateway.controller.publisher.hooks.ProgrammableGatewayDeployHistory.objects.filter")
    @patch("apigateway.controller.publisher.hooks.ProgrammableGatewayDeployHistory.objects.create")
    @patch("apigateway.controller.publisher.hooks.paas_app_module_offline")
    def test_programmable_gateway_offline_success(
        self,
        mock_offline,
        mock_create,
        mock_filter,
        mock_release,
        mock_release_history,
        mock_user_credentials,
    ):
        """Test successful programmable gateway offline"""
        mock_offline.return_value = "offline_operation_id"
        mock_last_deploy_history = Mock()
        mock_last_deploy_history.branch = "main"
        mock_last_deploy_history.commit_id = "abc123"
        mock_filter.return_value.first.return_value = mock_last_deploy_history

        _pre_publish_programmable_gateway_offline(
            PublishSourceEnum.GATEWAY_DISABLE,
            "test_user",
            mock_release,
            mock_release_history,
            mock_user_credentials,
        )

        # Verify paas_app_module_offline was called
        mock_offline.assert_called_once_with(
            app_code="test-gateway",
            module="default",
            env="prod",
            user_credentials=mock_user_credentials,
        )

        # Verify deploy history was queried
        mock_filter.assert_called_once_with(
            gateway=mock_release.gateway,
            version="v1.0.0",
        )

        # Verify new deploy history was created
        mock_create.assert_called_once_with(
            gateway=mock_release.gateway,
            stage=mock_release.stage,
            branch="main",
            version="v1.0.0",
            commit_id="abc123",
            deploy_id="offline_operation_id",
            publish_id=123,
            created_by="test_user",
            source=PublishSourceEnum.GATEWAY_DISABLE.value,
        )

    @patch("apigateway.controller.publisher.hooks.ProgrammableGatewayDeployHistory.objects.filter")
    @patch("apigateway.controller.publisher.hooks.paas_app_module_offline")
    def test_programmable_gateway_offline_no_deploy_history(
        self,
        mock_offline,
        mock_filter,
        mock_release,
        mock_release_history,
        mock_user_credentials,
    ):
        """Test programmable gateway offline when no deploy history exists"""
        mock_offline.return_value = "offline_operation_id"
        mock_filter.return_value.first.return_value = None

        with patch(
            "apigateway.controller.publisher.hooks.ProgrammableGatewayDeployHistory.objects.create"
        ) as mock_create:
            _pre_publish_programmable_gateway_offline(
                PublishSourceEnum.GATEWAY_DISABLE,
                "test_user",
                mock_release,
                mock_release_history,
                mock_user_credentials,
            )

            # Verify paas_app_module_offline was called
            mock_offline.assert_called_once()

            # Verify no new deploy history was created
            mock_create.assert_not_called()

    @patch("apigateway.controller.publisher.hooks.ProgrammableGatewayDeployHistory.objects.filter")
    @patch("apigateway.controller.publisher.hooks.paas_app_module_offline")
    def test_programmable_gateway_offline_with_different_source(
        self,
        mock_offline,
        mock_filter,
        mock_release,
        mock_release_history,
        mock_user_credentials,
    ):
        """Test programmable gateway offline with different source"""
        mock_offline.return_value = "offline_operation_id"
        mock_last_deploy_history = Mock()
        mock_last_deploy_history.branch = "develop"
        mock_last_deploy_history.commit_id = "def456"
        mock_filter.return_value.first.return_value = mock_last_deploy_history

        with patch(
            "apigateway.controller.publisher.hooks.ProgrammableGatewayDeployHistory.objects.create"
        ) as mock_create:
            _pre_publish_programmable_gateway_offline(
                PublishSourceEnum.STAGE_DISABLE,
                "admin_user",
                mock_release,
                mock_release_history,
                mock_user_credentials,
            )

            # Verify new deploy history was created with correct source
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["source"] == PublishSourceEnum.STAGE_DISABLE.value
            assert call_args["created_by"] == "admin_user"
