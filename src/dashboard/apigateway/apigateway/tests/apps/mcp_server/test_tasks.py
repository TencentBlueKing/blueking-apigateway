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

import pytest
from ddf import G

from apigateway.apps.mcp_server.models import MCPServer
from apigateway.apps.mcp_server.tasks import _fetch_updated_prompts, sync_mcp_server_after_release
from apigateway.core.constants import ReleaseHistoryStatusEnum
from apigateway.core.models import ReleaseHistory


class TestFetchUpdatedPrompts:
    def test_skip_invalid_payload_items(self, caplog):
        with (
            patch(
                "apigateway.apps.mcp_server.tasks.MCPServerPromptHandler.fetch_remote_prompts_by_ids",
                return_value=[{"id": 1, "name": "ok"}, {"name": "no-id"}, "invalid-item"],
            ),
            caplog.at_level("WARNING"),
        ):
            result = _fetch_updated_prompts({1, 2, 3})

        assert result == {1: {"id": 1, "name": "ok"}}
        assert "without id" in caplog.text
        assert "expected dict" in caplog.text


class TestSyncMcpServerAfterRelease:
    @pytest.fixture()
    def release_history(self, fake_gateway, fake_stage, fake_resource_version):
        return G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=fake_stage,
            resource_version=fake_resource_version,
        )

    def test_success(self, fake_gateway, fake_stage, release_history):
        """发布成功后写入 MCP Server"""
        mcp_data = [{"name": "s1", "description": "d", "resource_names": ["r1"], "tool_names": ["r1"]}]
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name=f"{fake_gateway.name}-{fake_stage.name}-s1",
            status=0,
        )

        with (
            patch(
                "apigateway.apps.mcp_server.tasks.wait_release_done",
                return_value=ReleaseHistoryStatusEnum.SUCCESS.value,
            ),
            patch(
                "apigateway.apps.mcp_server.tasks.MCPServerHandler.save_mcp_servers",
                return_value=[{"name": "s1", "action": "updated", "id": mcp_server.id}],
            ) as mock_save,
        ):
            sync_mcp_server_after_release(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                release_history_id=release_history.id,
                mcp_servers_data=mcp_data,
                username="open-api-user",
            )

        mock_save.assert_called_once_with(
            gateway_id=fake_gateway.id,
            gateway_name=fake_gateway.name,
            stage_id=fake_stage.id,
            stage_name=fake_stage.name,
            mcp_servers_data=mcp_data,
            username="open-api-user",
            comment=None,
        )

    def test_release_failed_skips_save(self, fake_gateway, fake_stage, release_history):
        """发布失败时跳过写入"""
        mcp_data = [{"name": "s1"}]

        with (
            patch(
                "apigateway.apps.mcp_server.tasks.wait_release_done",
                return_value=ReleaseHistoryStatusEnum.FAILURE.value,
            ),
            patch(
                "apigateway.apps.mcp_server.tasks.MCPServerHandler.save_mcp_servers",
            ) as mock_save,
        ):
            sync_mcp_server_after_release(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                release_history_id=release_history.id,
                mcp_servers_data=mcp_data,
            )

        mock_save.assert_not_called()

    def test_save_exception_logged(self, fake_gateway, fake_stage, release_history):
        """写入异常时不抛出，记录日志"""
        mcp_data = [{"name": "s1"}]

        with (
            patch(
                "apigateway.apps.mcp_server.tasks.wait_release_done",
                return_value=ReleaseHistoryStatusEnum.SUCCESS.value,
            ),
            patch(
                "apigateway.apps.mcp_server.tasks.MCPServerHandler.save_mcp_servers",
                side_effect=Exception("db error"),
            ),
        ):
            sync_mcp_server_after_release(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                release_history_id=release_history.id,
                mcp_servers_data=mcp_data,
            )
