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
import json
from unittest.mock import patch

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerExtendTypeEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerExtend
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.core.models import Gateway, Release, Resource, Stage
from apigateway.tests.utils.testing import create_gateway
from apigateway.utils.time import NeverExpiresTime


class TestMCPServerHandler:
    @pytest.fixture(autouse=True)
    def setup_fixtures(self):
        self.gateway = create_gateway()

    def test_virtual_app_code_prefix(self):
        assert MCPServerHandler._virtual_app_code_prefix(1) == "v_mcp_1_"

    def test_virtual_app_code(self):
        assert MCPServerHandler._virtual_app_code(1, "test") == "v_mcp_1_test"

    def test_cleanup_all_resource_permissions(self, fake_gateway):
        G(AppResourcePermission, gateway_id=fake_gateway.id, bk_app_code="v_mcp_1_test")

        MCPServerHandler._cleanup_all_resource_permissions(fake_gateway.id, 1)

        records = AppResourcePermission.objects.filter(gateway_id=fake_gateway.id, bk_app_code="v_mcp_1_test").all()
        assert len(records) == 0

    def test_disable_servers(self, fake_gateway, fake_stage):
        server1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        server2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)

        MCPServerHandler.disable_servers(gateway_id=fake_gateway.id, stage_id=0)

        server1.refresh_from_db()
        server2.refresh_from_db()

        assert server1.status == MCPServerStatusEnum.INACTIVE.value
        assert server2.status == MCPServerStatusEnum.INACTIVE.value

        # disable by specific stage
        server1.status = MCPServerStatusEnum.ACTIVE.value
        server1.save()

        MCPServerHandler.disable_servers(gateway_id=fake_gateway.id, stage_id=fake_stage.id)

        server1.refresh_from_db()

        assert server1.status == MCPServerStatusEnum.INACTIVE.value

    def test_sync_permissions_no_app_codes(self, fake_gateway, fake_stage):
        """Test sync_permissions when no app codes exist - should cleanup and return early"""
        # Create MCP server with no app permissions
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        # Create some existing permissions that should be cleaned up
        G(AppResourcePermission, gateway=fake_gateway, bk_app_code=f"v_mcp_{mcp_server.id}_test1", resource_id=1)
        G(AppResourcePermission, gateway=fake_gateway, bk_app_code=f"v_mcp_{mcp_server.id}_test2", resource_id=2)

        with patch.object(MCPServerHandler, "_cleanup_all_resource_permissions") as mock_cleanup:
            MCPServerHandler.sync_permissions(mcp_server.id)

            # Should call cleanup with correct parameters
            mock_cleanup.assert_called_once_with(gateway_id=fake_gateway.id, mcp_server_id=mcp_server.id)

    def test_sync_permissions_no_resource_names(self, fake_gateway, fake_stage):
        """Test sync_permissions when no resource names exist - should return early"""
        # Create MCP server with app permissions but no resource names
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.resource_names = []  # No resource names
        mcp_server.save()

        # Create app permission
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="test_app")

        with patch.object(MCPServerHandler, "_cleanup_all_resource_permissions") as mock_cleanup:
            MCPServerHandler.sync_permissions(mcp_server.id)

            # Should not call cleanup since we return early
            mock_cleanup.assert_not_called()

    def test_sync_permissions_no_changes(self, fake_gateway, fake_stage):
        """Test sync_permissions when current permissions match desired permissions - should return early"""
        # Create resources
        resource1 = G(Resource, gateway=fake_gateway, name="resource1")
        resource2 = G(Resource, gateway=fake_gateway, name="resource2")

        # Create MCP server with resource names
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.resource_names = ["resource1", "resource2"]
        mcp_server.save()

        # Create app permissions
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app1")
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app2")

        # Create existing permissions that match what should be created
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app1",
            resource_id=resource1.id,
            grant_type=GrantTypeEnum.SYNC.value,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app1",
            resource_id=resource2.id,
            grant_type=GrantTypeEnum.SYNC.value,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app2",
            resource_id=resource1.id,
            grant_type=GrantTypeEnum.SYNC.value,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app2",
            resource_id=resource2.id,
            grant_type=GrantTypeEnum.SYNC.value,
        )

        # Count existing permissions before sync
        initial_count = AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_").count()

        MCPServerHandler.sync_permissions(mcp_server.id)

        # Count should remain the same (no changes)
        final_count = AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_").count()

        assert initial_count == final_count == 4

    def test_sync_permissions_add_permissions(self, fake_gateway, fake_stage):
        """Test sync_permissions when new permissions need to be added"""
        # Create resources
        resource1 = G(Resource, gateway=fake_gateway, name="resource1")
        resource2 = G(Resource, gateway=fake_gateway, name="resource2")

        # Create MCP server with resource names
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.resource_names = ["resource1", "resource2"]
        mcp_server.save()

        # Create app permissions
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app1")
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app2")

        # No existing permissions
        assert AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_").count() == 0

        MCPServerHandler.sync_permissions(mcp_server.id)

        # Should create 4 permissions (2 apps × 2 resources)
        permissions = AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_")
        assert permissions.count() == 4

        # Verify permission details
        for permission in permissions:
            assert permission.gateway == fake_gateway
            assert permission.resource_id in [resource1.id, resource2.id]
            assert permission.bk_app_code in [f"v_mcp_{mcp_server.id}_app1", f"v_mcp_{mcp_server.id}_app2"]
            assert permission.expires == NeverExpiresTime.time
            assert permission.grant_type == GrantTypeEnum.SYNC.value

    def test_sync_permissions_delete_permissions(self, fake_gateway, fake_stage):
        """Test sync_permissions when existing permissions need to be deleted"""
        # Create resources
        resource1 = G(Resource, gateway=fake_gateway, name="resource1")
        resource2 = G(Resource, gateway=fake_gateway, name="resource2")

        # Create MCP server with only one resource name
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.resource_names = ["resource1"]  # Only resource1
        mcp_server.save()

        # Create app permission for only one app
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app1")

        # Create existing permissions for both resources and multiple apps (should be cleaned up)
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app1",
            resource_id=resource1.id,
        )
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app1",
            resource_id=resource2.id,
        )  # Should be deleted
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app2",  # Should be deleted
            resource_id=resource1.id,
        )

        assert AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_").count() == 3

        MCPServerHandler.sync_permissions(mcp_server.id)

        # Should only have 1 permission left (app1 × resource1)
        permissions = AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_")
        assert permissions.count() == 1

        permission = permissions.first()
        assert permission.bk_app_code == f"v_mcp_{mcp_server.id}_app1"
        assert permission.resource_id == resource1.id

    def test_sync_permissions_add_and_delete_permissions(self, fake_gateway, fake_stage):
        """Test sync_permissions when both adding and deleting permissions"""
        # Create resources
        resource1 = G(Resource, gateway=fake_gateway, name="resource1")
        resource2 = G(Resource, gateway=fake_gateway, name="resource2")
        resource3 = G(Resource, gateway=fake_gateway, name="resource3")

        # Create MCP server with resource names
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server.resource_names = ["resource2", "resource3"]  # Changed from resource1 to resource2,3
        mcp_server.save()

        # Create app permissions
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app1")
        G(MCPServerAppPermission, mcp_server=mcp_server, bk_app_code="app2")  # New app

        # Create existing permissions for resource1 and app1 (should be deleted)
        G(
            AppResourcePermission,
            gateway=fake_gateway,
            bk_app_code=f"v_mcp_{mcp_server.id}_app1",
            resource_id=resource1.id,
        )

        assert AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_").count() == 1

        MCPServerHandler.sync_permissions(mcp_server.id)

        # Should have 4 permissions (2 apps × 2 resources)
        permissions = AppResourcePermission.objects.filter(bk_app_code__startswith=f"v_mcp_{mcp_server.id}_")
        assert permissions.count() == 4

        # Verify no permissions for resource1
        assert not permissions.filter(resource_id=resource1.id).exists()

        # Verify permissions for resource2 and resource3
        assert permissions.filter(resource_id=resource2.id).count() == 2
        assert permissions.filter(resource_id=resource3.id).count() == 2

        # Verify permissions for both apps
        assert permissions.filter(bk_app_code=f"v_mcp_{mcp_server.id}_app1").count() == 2
        assert permissions.filter(bk_app_code=f"v_mcp_{mcp_server.id}_app2").count() == 2

    def test_get_valid_resource_names(self, fake_gateway, fake_stage, fake_resource_version):
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)

        expected_resource_names = {resource["name"] for resource in fake_resource_version.data}

        resource_names = MCPServerHandler().get_valid_resource_names(fake_gateway.id, fake_stage.id)
        assert resource_names == expected_resource_names

    def test_get_valid_resource_names_no_release(
        self,
    ):
        fake_gateway = G(Gateway, id=1)
        fake_stage = G(Stage, id=1)

        with pytest.raises(Exception):
            MCPServerHandler().get_valid_resource_names(fake_gateway.id, fake_stage.id)

    # ========== Prompts 相关方法测试 ==========

    def test_fetch_remote_prompts(self, mocker):
        """测试从远程获取 prompts 列表"""
        mock_prompts = [
            {"id": 1, "name": "Prompt 1", "code": "prompt_001"},
            {"id": 2, "name": "Prompt 2", "code": "prompt_002"},
        ]

        mock_credentials = mocker.MagicMock()

        with patch(
            "apigateway.biz.mcp_server.mcp_server.bkaidev.fetch_prompts_list", return_value=mock_prompts
        ) as mock_fetch:
            result = MCPServerHandler.fetch_remote_prompts(user_credentials=mock_credentials)

            mock_fetch.assert_called_once_with(user_credentials=mock_credentials)
            assert result == mock_prompts

    def test_get_prompts_empty(self, fake_gateway, fake_stage):
        """测试获取 prompts（无数据）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        result = MCPServerHandler.get_prompts(mcp_server.id)

        assert result == []

    def test_get_prompts_with_data(self, fake_gateway, fake_stage):
        """测试获取 prompts（有数据）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        prompts = [
            {"id": "prompt_001", "name": "代码审查助手"},
            {"id": "prompt_002", "name": "API 文档生成器"},
        ]

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(prompts),
        )

        result = MCPServerHandler.get_prompts(mcp_server.id)

        assert len(result) == 2
        assert result[0]["id"] == "prompt_001"
        assert result[1]["id"] == "prompt_002"

    def test_get_prompts_invalid_json(self, fake_gateway, fake_stage):
        """测试获取 prompts（无效 JSON）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content="invalid json",
        )

        result = MCPServerHandler.get_prompts(mcp_server.id)

        assert result == []

    def test_get_prompts_empty_content(self, fake_gateway, fake_stage):
        """测试获取 prompts（空内容）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content="",
        )

        result = MCPServerHandler.get_prompts(mcp_server.id)

        assert result == []

    def test_save_prompts_create(self, fake_gateway, fake_stage):
        """测试保存 prompts（创建新记录）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        prompts = [
            {"id": "prompt_001", "name": "代码审查助手"},
        ]

        MCPServerHandler.save_prompts(mcp_server.id, prompts, "admin")

        extend = MCPServerExtend.objects.get(
            mcp_server_id=mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )

        assert json.loads(extend.content) == prompts
        assert extend.created_by == "admin"
        assert extend.updated_by == "admin"

    def test_save_prompts_update(self, fake_gateway, fake_stage):
        """测试保存 prompts（更新已有记录）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        old_prompts = [{"id": "old_prompt"}]
        new_prompts = [{"id": "new_prompt", "name": "新 Prompt"}]

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(old_prompts),
            created_by="creator",
            updated_by="creator",
        )

        MCPServerHandler.save_prompts(mcp_server.id, new_prompts, "updater")

        extend = MCPServerExtend.objects.get(
            mcp_server_id=mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )

        assert json.loads(extend.content) == new_prompts
        assert extend.created_by == "creator"  # 创建者不变
        assert extend.updated_by == "updater"  # 更新者变化

    def test_delete_prompts(self, fake_gateway, fake_stage):
        """测试删除 prompts"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": "prompt_001"}]),
        )

        assert MCPServerExtend.objects.filter(
            mcp_server_id=mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).exists()

        MCPServerHandler.delete_prompts(mcp_server.id)

        assert not MCPServerExtend.objects.filter(
            mcp_server_id=mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).exists()

    def test_delete_prompts_not_exists(self, fake_gateway, fake_stage):
        """测试删除 prompts（不存在时不报错）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        # 不应抛出异常
        MCPServerHandler.delete_prompts(mcp_server.id)

    def test_get_prompts_count_empty(self, fake_gateway, fake_stage):
        """测试获取 prompts 数量（无数据）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        result = MCPServerHandler.get_prompts_count(mcp_server.id)

        assert result == 0

    def test_get_prompts_count_with_data(self, fake_gateway, fake_stage):
        """测试获取 prompts 数量（有数据）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        prompts = [
            {"id": "prompt_001", "name": "代码审查助手"},
            {"id": "prompt_002", "name": "API 文档生成器"},
            {"id": "prompt_003", "name": "测试用例生成器"},
        ]

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(prompts),
        )

        result = MCPServerHandler.get_prompts_count(mcp_server.id)

        assert result == 3

    def test_get_prompts_count_map_empty(self, fake_gateway, fake_stage):
        """测试批量获取 prompts 数量（无数据）"""
        mcp_server1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        result = MCPServerHandler.get_prompts_count_map([mcp_server1.id, mcp_server2.id])

        assert result == {mcp_server1.id: 0, mcp_server2.id: 0}

    def test_get_prompts_count_map_with_data(self, fake_gateway, fake_stage):
        """测试批量获取 prompts 数量（有数据）"""
        mcp_server1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server3 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        # mcp_server1 有 2 个 prompts
        G(
            MCPServerExtend,
            mcp_server=mcp_server1,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": 1}, {"id": 2}]),
        )

        # mcp_server2 有 3 个 prompts
        G(
            MCPServerExtend,
            mcp_server=mcp_server2,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": 1}, {"id": 2}, {"id": 3}]),
        )

        # mcp_server3 没有 prompts

        result = MCPServerHandler.get_prompts_count_map([mcp_server1.id, mcp_server2.id, mcp_server3.id])

        assert result == {mcp_server1.id: 2, mcp_server2.id: 3, mcp_server3.id: 0}

    def test_get_prompts_count_map_invalid_json(self, fake_gateway, fake_stage):
        """测试批量获取 prompts 数量（无效 JSON）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content="invalid json",
        )

        result = MCPServerHandler.get_prompts_count_map([mcp_server.id])

        assert result == {mcp_server.id: 0}

    def test_get_prompts_count_map_empty_content(self, fake_gateway, fake_stage):
        """测试批量获取 prompts 数量（空内容）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content="",
        )

        result = MCPServerHandler.get_prompts_count_map([mcp_server.id])

        assert result == {mcp_server.id: 0}
