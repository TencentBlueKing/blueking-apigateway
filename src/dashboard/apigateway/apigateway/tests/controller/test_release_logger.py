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
import logging
import uuid

import pytest

from apigateway.controller.release_logger import ReleaseProcedureLogger


class TestReleaseProcedureLogger:
    """Test ReleaseProcedureLogger class"""

    @pytest.fixture
    def mock_gateway(self, mocker):
        """Create a mock gateway"""
        gateway = mocker.Mock()
        gateway.name = "test-gateway"
        gateway.id = 123
        return gateway

    @pytest.fixture
    def mock_stage(self, mocker):
        """Create a mock stage"""
        stage = mocker.Mock()
        stage.name = "prod"
        stage.id = 456
        return stage

    @pytest.fixture
    def mock_logger(self, mocker):
        """Create a mock logger"""
        return mocker.Mock(spec=logging.Logger)

    def test_init_with_gateway_only(self, mock_gateway, mock_logger):
        """Test initialization with gateway only"""
        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
        )

        assert logger.name == "test-procedure"
        assert logger._gateway == mock_gateway
        assert logger._stage is None
        assert logger._publish_id is None
        assert logger.release_task_id is not None  # Should be generated
        # Verify UUID format
        assert isinstance(uuid.UUID(logger.release_task_id), uuid.UUID)

    def test_init_with_gateway_and_stage(self, mock_gateway, mock_stage, mock_logger):
        """Test initialization with gateway and stage"""
        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
            stage=mock_stage,
        )

        assert logger._gateway == mock_gateway
        assert logger._stage == mock_stage
        assert logger._stage.name == "prod"

    def test_init_with_all_parameters(self, mock_gateway, mock_stage, mock_logger):
        """Test initialization with all parameters"""
        task_id = "custom-task-id"
        publish_id = 789

        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
            stage=mock_stage,
            release_task_id=task_id,
            publish_id=publish_id,
        )

        assert logger.release_task_id == task_id
        assert logger._publish_id == publish_id

    def test_message_prefix_gateway_only(self, mock_gateway, mock_logger):
        """Test message prefix with gateway only"""
        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
            release_task_id="test-task-123",
        )

        prefix = logger._message_prefix
        assert "procedure test-procedure:" in prefix
        assert "gateway=test-gateway(123)" in prefix
        assert "release_task_id=test-task-123" in prefix
        assert "stage=" not in prefix  # Stage should not be in prefix
        assert "publish_id=" not in prefix  # Publish ID should not be in prefix

    def test_message_prefix_with_stage(self, mock_gateway, mock_stage, mock_logger):
        """Test message prefix with gateway and stage"""
        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
            stage=mock_stage,
            release_task_id="test-task-456",
        )

        prefix = logger._message_prefix
        assert "procedure test-procedure:" in prefix
        assert "gateway=test-gateway(123)" in prefix
        assert "stage=prod(456)" in prefix
        assert "release_task_id=test-task-456" in prefix

    def test_message_prefix_with_all_info(self, mock_gateway, mock_stage, mock_logger):
        """Test message prefix with all information"""
        logger = ReleaseProcedureLogger(
            name="release-to-prod",
            logger=mock_logger,
            gateway=mock_gateway,
            stage=mock_stage,
            release_task_id="task-xyz",
            publish_id=999,
        )

        prefix = logger._message_prefix
        assert "procedure release-to-prod:" in prefix
        assert "gateway=test-gateway(123)" in prefix
        assert "stage=prod(456)" in prefix
        assert "publish_id=999" in prefix
        assert "release_task_id=task-xyz" in prefix

    def test_auto_generated_release_task_id_is_valid_uuid(self, mock_gateway, mock_logger):
        """Test that auto-generated release task ID is a valid UUID"""
        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
        )

        # Should be able to parse as UUID without raising exception
        task_id = logger.release_task_id
        uuid_obj = uuid.UUID(task_id)
        assert str(uuid_obj) == task_id

    def test_multiple_instances_have_different_task_ids(self, mock_gateway, mock_logger):
        """Test that multiple instances without explicit task_id get unique IDs"""
        logger1 = ReleaseProcedureLogger(
            name="test-procedure-1",
            logger=mock_logger,
            gateway=mock_gateway,
        )

        logger2 = ReleaseProcedureLogger(
            name="test-procedure-2",
            logger=mock_logger,
            gateway=mock_gateway,
        )

        assert logger1.release_task_id != logger2.release_task_id

    def test_custom_release_task_id_is_preserved(self, mock_gateway, mock_logger):
        """Test that custom release task ID is preserved"""
        custom_id = "my-custom-task-id"
        logger = ReleaseProcedureLogger(
            name="test-procedure",
            logger=mock_logger,
            gateway=mock_gateway,
            release_task_id=custom_id,
        )

        assert logger.release_task_id == custom_id

    def test_message_prefix_format(self, mock_gateway, mock_stage, mock_logger):
        """Test the exact format of message prefix"""
        logger = ReleaseProcedureLogger(
            name="deploy",
            logger=mock_logger,
            gateway=mock_gateway,
            stage=mock_stage,
            release_task_id="abc-123",
            publish_id=555,
        )

        prefix = logger._message_prefix
        expected = (
            "procedure deploy: gateway=test-gateway(123), stage=prod(456), publish_id=555, release_task_id=abc-123"
        )
        assert prefix == expected

    def test_publish_id_none_not_in_prefix(self, mock_gateway, mock_stage, mock_logger):
        """Test that when publish_id is None, it's not included in prefix"""
        logger = ReleaseProcedureLogger(
            name="test",
            logger=mock_logger,
            gateway=mock_gateway,
            stage=mock_stage,
            release_task_id="test-123",
            publish_id=None,
        )

        prefix = logger._message_prefix
        assert "publish_id" not in prefix
