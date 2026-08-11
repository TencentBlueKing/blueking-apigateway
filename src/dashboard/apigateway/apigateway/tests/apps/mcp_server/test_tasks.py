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
from unittest.mock import Mock, call, patch

import pytest
from ddf import G

from apigateway.apps.mcp_server.models import MCPServer
from apigateway.apps.mcp_server.tasks import (
    _fetch_updated_prompts,
    add_stage_mcp_server_permissions_before_release_update,
    reconcile_stage_mcp_server_permissions_after_release,
    sync_mcp_server_after_release,
)
from apigateway.core.constants import ReleaseHistoryStatusEnum
from apigateway.core.models import Release, ReleaseHistory, ResourceVersion


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


class TestStageMcpServerPermissionSync:
    @pytest.fixture(autouse=True)
    def mock_permission_sync_lock(self):
        lock = Mock()
        lock.acquire.return_value = True
        with patch(
            "apigateway.apps.mcp_server.tasks.redis_lock.Lock",
            return_value=lock,
        ) as lock_constructor:
            yield lock_constructor

    def test_add_skips_stage_without_mcp_servers(self, fake_stage, mock_permission_sync_lock):
        with patch("apigateway.apps.mcp_server.tasks.ResourceVersion.objects.filter") as mock_filter:
            add_stage_mcp_server_permissions_before_release_update(
                stage_id=fake_stage.id,
                resource_version_id=1,
            )

        mock_permission_sync_lock.assert_not_called()
        mock_filter.assert_not_called()

    def test_reconcile_skips_stage_without_mcp_servers(self, fake_stage, mock_permission_sync_lock):
        with patch("apigateway.apps.mcp_server.tasks.Release.objects.filter") as mock_filter:
            reconcile_stage_mcp_server_permissions_after_release(
                stage_id=fake_stage.id,
                expected_resource_version_id=1,
                expected_release_history_id=1,
            )

        mock_permission_sync_lock.assert_not_called()
        mock_filter.assert_not_called()

    def test_adds_permissions_from_explicit_resource_version(self, fake_gateway, fake_stage):
        resource_version = G(ResourceVersion, gateway=fake_gateway)
        mcp_servers = [
            G(MCPServer, gateway=fake_gateway, stage=fake_stage),
            G(MCPServer, gateway=fake_gateway, stage=fake_stage),
        ]

        with patch("apigateway.apps.mcp_server.tasks.MCPServerHandler.sync_permissions") as mock_sync:
            add_stage_mcp_server_permissions_before_release_update(
                stage_id=fake_stage.id,
                resource_version_id=resource_version.id,
            )

        mock_sync.assert_has_calls(
            [
                call(mcp_servers[0].id, resource_version=resource_version, delete_stale=False),
                call(mcp_servers[1].id, resource_version=resource_version, delete_stale=False),
            ],
            any_order=True,
        )

    def test_strong_sync_uses_current_release(self, fake_gateway, fake_stage, fake_resource_version):
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        with patch("apigateway.apps.mcp_server.tasks.MCPServerHandler.sync_permissions") as mock_sync:
            reconcile_stage_mcp_server_permissions_after_release(
                stage_id=fake_stage.id,
                expected_resource_version_id=fake_resource_version.id,
                expected_release_history_id=1,
            )

        mock_sync.assert_called_once_with(
            mcp_server.id,
            resource_version=fake_resource_version,
            delete_stale=True,
        )

    def test_missing_explicit_resource_version_is_logged_and_skipped(self, fake_gateway, fake_stage, caplog):
        G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        missing_resource_version_id = 999999

        with (
            patch("apigateway.apps.mcp_server.tasks.MCPServerHandler.sync_permissions") as mock_sync,
            caplog.at_level("WARNING"),
        ):
            add_stage_mcp_server_permissions_before_release_update(
                stage_id=fake_stage.id,
                resource_version_id=missing_resource_version_id,
            )

        mock_sync.assert_not_called()
        assert f"resource_version_id={missing_resource_version_id}" in caplog.text

    def test_handler_failure_is_logged_without_stopping_other_servers(
        self, fake_gateway, fake_stage, fake_resource_version, caplog
    ):
        mcp_servers = [
            G(MCPServer, gateway=fake_gateway, stage=fake_stage),
            G(MCPServer, gateway=fake_gateway, stage=fake_stage),
        ]

        with (
            patch(
                "apigateway.apps.mcp_server.tasks.MCPServerHandler.sync_permissions",
                side_effect=[RuntimeError("database unavailable"), None],
            ) as mock_sync,
            caplog.at_level("ERROR"),
        ):
            add_stage_mcp_server_permissions_before_release_update(
                stage_id=fake_stage.id,
                resource_version_id=fake_resource_version.id,
            )

        assert mock_sync.call_count == 2
        assert f"mcp_server_id={mcp_servers[0].id}" in caplog.text

    def test_cleanup_skips_when_a_newer_resource_version_publish_has_started(
        self, fake_gateway, fake_stage, fake_resource_version
    ):
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)
        current_history = G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=fake_stage,
            resource_version=fake_resource_version,
        )
        newer_resource_version = G(ResourceVersion, gateway=fake_gateway)
        G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=fake_stage,
            resource_version=newer_resource_version,
        )
        G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        with patch("apigateway.apps.mcp_server.tasks.MCPServerHandler.sync_permissions") as mock_sync:
            reconcile_stage_mcp_server_permissions_after_release(
                stage_id=fake_stage.id,
                expected_resource_version_id=fake_resource_version.id,
                expected_release_history_id=current_history.id,
            )

        mock_sync.assert_not_called()

    def test_strong_sync_skips_when_release_has_changed(self, fake_gateway, fake_stage, fake_resource_version):
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)
        G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        with patch("apigateway.apps.mcp_server.tasks.MCPServerHandler.sync_permissions") as mock_sync:
            reconcile_stage_mcp_server_permissions_after_release(
                stage_id=fake_stage.id,
                expected_resource_version_id=fake_resource_version.id + 1,
                expected_release_history_id=1,
            )

        mock_sync.assert_not_called()


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
