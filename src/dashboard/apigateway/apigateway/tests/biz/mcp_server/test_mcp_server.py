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

from apigateway.apps.mcp_server.constants import (
    OFFICIAL_MCP_CATEGORY_NAME,
    MCPServerExtendTypeEnum,
    MCPServerLeastPrivilegeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission, MCPServerCategory, MCPServerExtend
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum
from apigateway.core.models import Gateway, Release, Resource, ResourceVersion, Stage
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
        mcp_server._resource_names = ""  # No resource names
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
        mcp_server._resource_names = "resource1;resource2"
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
        mcp_server._resource_names = "resource1;resource2"
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
        mcp_server._resource_names = "resource1"  # Only resource1
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
        mcp_server._resource_names = "resource2;resource3"  # Changed from resource1 to resource2,3
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

    # ========== 应用态权限安全风险检测测试 ==========

    @staticmethod
    def _make_resource_version_with_data(gateway, resources):
        """构造带有指定资源数据的 ResourceVersion

        resources 中每个元素支持的 key：
            - name: 资源名称（必需）
            - app_verified_required: 是否需要应用认证（默认 True）
            - resource_perm_required: 是否需要资源权限（默认 True）
            - auth_verified_required: 是否需要用户认证（默认 False）
            - skip_auth_verification: 是否跳过认证（默认 False）
        """
        rv = G(ResourceVersion, gateway=gateway)
        data = []
        for i, res in enumerate(resources):
            data.append(
                {
                    "id": i + 1,
                    "name": res["name"],
                    "description": f"test resource {res['name']}",
                    "method": "GET",
                    "path": f"/test/{res['name']}/",
                    "match_subpath": False,
                    "is_public": True,
                    "allow_apply_permission": True,
                    "api_labels": [],
                    "contexts": {
                        "resource_auth": {
                            "config": json.dumps(
                                {
                                    "app_verified_required": res.get("app_verified_required", True),
                                    "resource_perm_required": res.get("resource_perm_required", True),
                                    "auth_verified_required": res.get("auth_verified_required", False),
                                    "skip_auth_verification": res.get("skip_auth_verification", False),
                                }
                            )
                        }
                    },
                }
            )
        rv._data = json.dumps(data)
        rv.save()
        return rv

    def test_get_app_permission_risks_empty_when_oauth2_disabled(self, fake_gateway, fake_stage):
        """oauth2_public_client_enabled=False 时返回空"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=False,
            _resource_names="tool_a",
        )

        result = MCPServerHandler.get_app_permission_risks([mcp_server])

        assert result == {}

    def test_get_app_permission_risks_with_risky_tools(self, fake_gateway, fake_stage):
        """oauth2 开启且工具需要应用认证时，返回风险工具"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_a", "app_verified_required": True},
                {"name": "tool_b", "app_verified_required": False},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="tool_a;tool_b",
        )

        result = MCPServerHandler.get_app_permission_risks([mcp_server])

        assert mcp_server.id in result
        assert "tool_a" in result[mcp_server.id]
        assert "tool_b" not in result[mcp_server.id]

    def test_get_app_permission_risks_no_risk_when_all_tools_skip_app_auth(self, fake_gateway, fake_stage):
        """oauth2 开启但所有工具都不需要应用认证时无风险"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_c", "app_verified_required": False},
                {"name": "tool_d", "app_verified_required": False},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="tool_c;tool_d",
        )

        result = MCPServerHandler.get_app_permission_risks([mcp_server])

        assert result == {}

    def test_get_app_permission_risks_no_risk_when_no_release(self, fake_gateway, fake_stage):
        """oauth2 开启但未发布时无风险（无 Release 记录）"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="tool_e",
        )

        result = MCPServerHandler.get_app_permission_risks([mcp_server])

        assert result == {}

    def test_get_app_permission_risks_returns_tool_name_instead_of_resource_name(self, fake_gateway, fake_stage):
        """当资源配置了自定义 tool_name 时，返回 tool_name 而非 resource_name"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "get_user_info", "app_verified_required": True},
                {"name": "list_orders", "app_verified_required": True},
                {"name": "health_check", "app_verified_required": False},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="get_user_info@query_user;list_orders@order_list;health_check@ping",
        )

        result = MCPServerHandler.get_app_permission_risks([mcp_server])

        assert mcp_server.id in result
        assert "query_user" in result[mcp_server.id]
        assert "order_list" in result[mcp_server.id]
        assert "get_user_info" not in result[mcp_server.id]
        assert "list_orders" not in result[mcp_server.id]
        assert "ping" not in result[mcp_server.id]

    def test_get_app_permission_risks_multiple_mcp_servers(self, fake_gateway, fake_stage):
        """批量检测多个 MCPServer，混合 oauth2 开启/关闭"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_x", "app_verified_required": True},
                {"name": "tool_y", "app_verified_required": False},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_oauth2_on = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="tool_x;tool_y",
        )
        mcp_oauth2_off = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=False,
            _resource_names="tool_x",
        )

        result = MCPServerHandler.get_app_permission_risks([mcp_oauth2_on, mcp_oauth2_off])

        assert mcp_oauth2_on.id in result
        assert "tool_x" in result[mcp_oauth2_on.id]
        assert mcp_oauth2_off.id not in result

    # ========== Release 查询提取 & 共享测试 ==========

    def test_get_releases_for_mcp_servers(self, fake_gateway, fake_stage):
        """_get_releases_for_mcp_servers 应按 (gateway_id, stage_id) 返回 Release"""
        rv = self._make_resource_version_with_data(fake_gateway, [{"name": "tool_a"}])
        release = G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        result = MCPServerHandler._get_releases_for_mcp_servers([mcp_server])

        assert (fake_gateway.id, fake_stage.id) in result
        assert result[(fake_gateway.id, fake_stage.id)].id == release.id

    def test_get_releases_for_mcp_servers_empty(self):
        """空列表应返回空字典"""
        result = MCPServerHandler._get_releases_for_mcp_servers([])
        assert result == {}

    def test_get_releases_for_mcp_servers_no_release(self, fake_gateway, fake_stage):
        """无 Release 记录时返回空字典"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        result = MCPServerHandler._get_releases_for_mcp_servers([mcp_server])

        assert result == {}

    def test_get_app_permission_risks_with_shared_releases(self, fake_gateway, fake_stage):
        """传入预查询的 releases 参数，应复用而非重新查询"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [{"name": "tool_a", "app_verified_required": True}],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="tool_a",
        )

        releases = MCPServerHandler._get_releases_for_mcp_servers([mcp_server])
        result = MCPServerHandler.get_app_permission_risks([mcp_server], releases=releases)

        assert mcp_server.id in result
        assert "tool_a" in result[mcp_server.id]

    # ========== 最低权限级别计算测试 ==========

    def test_get_least_privileges_all_application(self, fake_gateway, fake_stage):
        """所有工具都不需要用户认证时，应返回 APPLICATION"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_a", "auth_verified_required": False},
                {"name": "tool_b", "auth_verified_required": False},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a;tool_b")

        result = MCPServerHandler.get_least_privileges([mcp_server])

        key = (fake_gateway.id, fake_stage.id)
        assert result[key] == MCPServerLeastPrivilegeEnum.APPLICATION.value

    def test_get_least_privileges_has_user_required(self, fake_gateway, fake_stage):
        """存在需要用户认证的工具时，应返回 APPLICATION_AND_USER"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_a", "auth_verified_required": False},
                {"name": "tool_b", "auth_verified_required": True},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a;tool_b")

        result = MCPServerHandler.get_least_privileges([mcp_server])

        key = (fake_gateway.id, fake_stage.id)
        assert result[key] == MCPServerLeastPrivilegeEnum.APPLICATION_AND_USER.value

    def test_get_least_privileges_skip_auth_verification(self, fake_gateway, fake_stage):
        """skip_auth_verification=True 时即使 auth_verified_required=True 也视为不需要用户认证"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_a", "auth_verified_required": True, "skip_auth_verification": True},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        result = MCPServerHandler.get_least_privileges([mcp_server])

        key = (fake_gateway.id, fake_stage.id)
        assert result[key] == MCPServerLeastPrivilegeEnum.APPLICATION.value

    def test_get_least_privileges_empty(self):
        """空列表应返回空字典"""
        result = MCPServerHandler.get_least_privileges([])
        assert result == {}

    def test_get_least_privileges_no_release(self, fake_gateway, fake_stage):
        """无 Release 记录时返回空字典"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        result = MCPServerHandler.get_least_privileges([mcp_server])

        assert result == {}

    def test_get_least_privileges_only_checks_relevant_tools(self, fake_gateway, fake_stage):
        """仅检查 MCP Server 关联的工具，不受其他资源影响"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_a", "auth_verified_required": False},
                {"name": "tool_b", "auth_verified_required": True},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        result = MCPServerHandler.get_least_privileges([mcp_server])

        key = (fake_gateway.id, fake_stage.id)
        assert result[key] == MCPServerLeastPrivilegeEnum.APPLICATION.value

    def test_get_least_privileges_with_shared_releases(self, fake_gateway, fake_stage):
        """传入预查询的 releases 参数，应复用而非重新查询"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [{"name": "tool_a", "auth_verified_required": True}],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        releases = MCPServerHandler._get_releases_for_mcp_servers([mcp_server])
        result = MCPServerHandler.get_least_privileges([mcp_server], releases=releases)

        key = (fake_gateway.id, fake_stage.id)
        assert result[key] == MCPServerLeastPrivilegeEnum.APPLICATION_AND_USER.value

    def test_shared_releases_between_risks_and_privileges(self, fake_gateway, fake_stage):
        """验证同一份 releases 可同时传给 get_app_permission_risks 和 get_least_privileges"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [
                {"name": "tool_a", "app_verified_required": True, "auth_verified_required": True},
                {"name": "tool_b", "app_verified_required": False, "auth_verified_required": False},
            ],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            oauth2_public_client_enabled=True,
            _resource_names="tool_a;tool_b",
        )

        releases = MCPServerHandler._get_releases_for_mcp_servers([mcp_server])
        risks = MCPServerHandler.get_app_permission_risks([mcp_server], releases=releases)
        privileges = MCPServerHandler.get_least_privileges([mcp_server], releases=releases)

        assert mcp_server.id in risks
        assert "tool_a" in risks[mcp_server.id]
        key = (fake_gateway.id, fake_stage.id)
        assert privileges[key] == MCPServerLeastPrivilegeEnum.APPLICATION_AND_USER.value

    # ========== validate_access 测试 ==========

    def test_validate_access_ok(self, fake_gateway, fake_stage):
        """正常情况：状态均为 ACTIVE，校验通过"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

        # 不应抛出异常
        MCPServerHandler.validate_access(mcp_server)

    def test_validate_access_inactive_server(self, fake_gateway, fake_stage):
        """MCPServer 未启用时应抛出 NOT_FOUND"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.INACTIVE.value,
            is_public=True,
        )

        with pytest.raises(Exception):
            MCPServerHandler.validate_access(mcp_server)

    def test_validate_access_inactive_gateway(self, fake_gateway, fake_stage):
        """网关未启用时应抛出 NOT_FOUND"""
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

        with pytest.raises(Exception):
            MCPServerHandler.validate_access(mcp_server)

    def test_validate_access_inactive_stage(self, fake_gateway, fake_stage):
        """环境未启用时应抛出 NOT_FOUND"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.INACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

        with pytest.raises(Exception):
            MCPServerHandler.validate_access(mcp_server)

    def test_validate_access_check_public_not_public(self, fake_gateway, fake_stage):
        """check_public=True 时，非公开且非维护者应抛出 NOT_FOUND"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway._maintainers = "admin"
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=False,
        )

        with pytest.raises(Exception):
            MCPServerHandler.validate_access(mcp_server, check_public=True, username="other_user")

    def test_validate_access_check_public_maintainer_allowed(self, fake_gateway, fake_stage):
        """check_public=True 时，非公开但是维护者可以访问"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway._maintainers = "admin"
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=False,
        )

        # 维护者不应抛异常
        MCPServerHandler.validate_access(mcp_server, check_public=True, username="admin")

    def test_validate_access_check_public_is_public(self, fake_gateway, fake_stage):
        """check_public=True 时，公开的 MCPServer 无需检查维护者"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )

        # 公开的 MCPServer，任何用户都可以访问
        MCPServerHandler.validate_access(mcp_server, check_public=True, username="anyone")

    def test_validate_access_check_public_no_username(self, fake_gateway, fake_stage):
        """check_public=True 且 is_public=False，不传 username 应抛出 NOT_FOUND"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=False,
        )

        with pytest.raises(Exception):
            MCPServerHandler.validate_access(mcp_server, check_public=True)

    # ========== build_guideline 测试 ==========

    def test_build_guideline(self, fake_gateway, fake_stage, mocker):
        """测试 build_guideline 返回渲染后的内容"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            name="test-mcp",
            description="A test MCP server",
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.render_to_string",
            return_value="# Guideline for test-mcp",
        )

        result = MCPServerHandler.build_guideline(mcp_server, user_tenant_id="tenant_1")

        assert result == "# Guideline for test-mcp"

    def test_build_guideline_with_least_privilege(self, fake_gateway, fake_stage, mocker):
        """测试 build_guideline 传入 least_privilege 参数"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            name="test-mcp",
        )

        mock_render = mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.render_to_string",
            return_value="# Guideline",
        )

        MCPServerHandler.build_guideline(
            mcp_server,
            least_privilege=MCPServerLeastPrivilegeEnum.APPLICATION.value,
        )

        # 验证 render_to_string 被调用
        mock_render.assert_called_once()

    # ========== apply_category_filter 测试 ==========

    def test_apply_category_filter_empty(self, fake_gateway, fake_stage):
        """空分类列表不做过滤"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        queryset = MCPServer.objects.filter(id=mcp_server.id)

        result = MCPServerHandler.apply_category_filter(queryset, [])

        assert list(result) == list(queryset)

    def test_apply_category_filter_or_logic(self, fake_gateway, fake_stage):
        """不包含特殊分类时使用 OR 逻辑"""
        MCPServerCategory.objects.all().delete()

        cat_a = G(MCPServerCategory, name="CatA", is_active=True)
        cat_b = G(MCPServerCategory, name="CatB", is_active=True)

        server_a = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        server_a.categories.add(cat_a)

        server_b = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        server_b.categories.add(cat_b)

        server_none = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        queryset = MCPServer.objects.filter(gateway=fake_gateway)
        result = MCPServerHandler.apply_category_filter(queryset, ["CatA", "CatB"])

        result_ids = set(result.values_list("id", flat=True))
        assert server_a.id in result_ids
        assert server_b.id in result_ids
        assert server_none.id not in result_ids

    def test_apply_category_filter_and_logic_with_special(self, fake_gateway, fake_stage):
        """包含 Official 分类时使用 AND 逻辑"""
        MCPServerCategory.objects.all().delete()

        official_cat = G(MCPServerCategory, name=OFFICIAL_MCP_CATEGORY_NAME, is_active=True)
        devops_cat = G(MCPServerCategory, name="DevOps", is_active=True)

        # 同时属于两个分类的 server
        server_both = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        server_both.categories.add(official_cat, devops_cat)

        # 只属于一个分类的 server
        server_official_only = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        server_official_only.categories.add(official_cat)

        queryset = MCPServer.objects.filter(gateway=fake_gateway)
        result = MCPServerHandler.apply_category_filter(queryset, [OFFICIAL_MCP_CATEGORY_NAME, "DevOps"])

        result_ids = set(result.values_list("id", flat=True))
        assert server_both.id in result_ids
        assert server_official_only.id not in result_ids

    def test_apply_category_filter_inactive_category(self, fake_gateway, fake_stage):
        """未激活的分类不匹配"""
        MCPServerCategory.objects.all().delete()

        inactive_cat = G(MCPServerCategory, name="InactiveCat", is_active=False)
        server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        server.categories.add(inactive_cat)

        queryset = MCPServer.objects.filter(gateway=fake_gateway)
        result = MCPServerHandler.apply_category_filter(queryset, ["InactiveCat"])

        assert result.count() == 0

    # ========== build_list_queryset 测试 ==========

    def test_build_list_queryset_basic(self, fake_gateway, fake_stage):
        """基础查询：只返回 ACTIVE 的 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        active_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )
        inactive_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.INACTIVE.value,
        )

        result = MCPServerHandler.build_list_queryset()
        result_ids = set(result.values_list("id", flat=True))

        assert active_server.id in result_ids
        assert inactive_server.id not in result_ids

    def test_build_list_queryset_with_keyword(self, fake_gateway, fake_stage):
        """关键字过滤"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            name="unique_keyword_test",
        )

        result = MCPServerHandler.build_list_queryset(keyword="unique_keyword")
        result_ids = set(result.values_list("id", flat=True))
        assert server.id in result_ids

        result_empty = MCPServerHandler.build_list_queryset(keyword="nonexistent_xyz")
        assert server.id not in set(result_empty.values_list("id", flat=True))

    def test_build_list_queryset_with_is_public(self, fake_gateway, fake_stage):
        """按 is_public 过滤"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        public_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
        )
        private_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=False,
        )

        result_public = MCPServerHandler.build_list_queryset(is_public=True)
        result_public_ids = set(result_public.values_list("id", flat=True))
        assert public_server.id in result_public_ids
        assert private_server.id not in result_public_ids

        result_private = MCPServerHandler.build_list_queryset(is_public=False)
        result_private_ids = set(result_private.values_list("id", flat=True))
        assert private_server.id in result_private_ids
        assert public_server.id not in result_private_ids

    def test_build_list_queryset_with_category(self, fake_gateway, fake_stage):
        """按单个分类过滤"""
        MCPServerCategory.objects.all().delete()

        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        cat = G(MCPServerCategory, name="TestCat", is_active=True)
        server_with_cat = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server_with_cat.categories.add(cat)

        server_no_cat = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        result = MCPServerHandler.build_list_queryset(category="TestCat")
        result_ids = set(result.values_list("id", flat=True))
        assert server_with_cat.id in result_ids
        assert server_no_cat.id not in result_ids

    def test_build_list_queryset_with_categories(self, fake_gateway, fake_stage):
        """按多个分类过滤"""
        MCPServerCategory.objects.all().delete()

        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        cat_a = G(MCPServerCategory, name="CatA", is_active=True)
        cat_b = G(MCPServerCategory, name="CatB", is_active=True)

        server_a = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server_a.categories.add(cat_a)

        server_b = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        server_b.categories.add(cat_b)

        result = MCPServerHandler.build_list_queryset(categories=["CatA", "CatB"])
        result_ids = set(result.values_list("id", flat=True))
        assert server_a.id in result_ids
        assert server_b.id in result_ids

    def test_build_list_queryset_inactive_gateway_excluded(self, fake_gateway, fake_stage):
        """网关未启用的 MCPServer 应被排除"""
        fake_gateway.status = GatewayStatusEnum.INACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )

        result = MCPServerHandler.build_list_queryset()
        assert server.id not in set(result.values_list("id", flat=True))

    # ========== build_list_context 测试 ==========

    def test_build_list_context_basic(self, fake_gateway, fake_stage):
        """基础上下文包含 gateways 和 stages"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        context = MCPServerHandler.build_list_context([mcp_server])

        assert "gateways" in context
        assert "stages" in context
        assert fake_gateway.id in context["gateways"]
        assert fake_stage.id in context["stages"]

    def test_build_list_context_with_prompts_count(self, fake_gateway, fake_stage):
        """include_prompts_count=True 时包含 prompts_count_map"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": 1}, {"id": 2}]),
        )

        context = MCPServerHandler.build_list_context([mcp_server], include_prompts_count=True)

        assert "prompts_count_map" in context
        assert context["prompts_count_map"][mcp_server.id] == 2

    def test_build_list_context_with_least_privileges(self, fake_gateway, fake_stage):
        """include_least_privileges=True 时包含 least_privileges"""
        rv = self._make_resource_version_with_data(
            fake_gateway,
            [{"name": "tool_a", "auth_verified_required": False}],
        )
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=rv)

        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, _resource_names="tool_a")

        context = MCPServerHandler.build_list_context([mcp_server], include_least_privileges=True)

        assert "least_privileges" in context
        key = (fake_gateway.id, fake_stage.id)
        assert key in context["least_privileges"]

    def test_build_list_context_empty(self, fake_gateway):
        """空列表应返回空 gateways/stages"""
        context = MCPServerHandler.build_list_context([])

        assert context["gateways"] == {}
        assert context["stages"] == {}

    # ========== build_retrieve_context 测试 ==========

    def test_build_retrieve_context_ok(self, fake_gateway, fake_stage, mocker):
        """正常情况下返回完整上下文"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=True,
            _resource_names="tool_a",
        )

        mocker.patch(
            "apigateway.biz.mcp_server.mcp_server.render_to_string",
            return_value="# Guideline",
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], {}),
        )

        context = MCPServerHandler.build_retrieve_context(mcp_server)

        assert "gateways" in context
        assert "stages" in context
        assert "labels" in context
        assert "tool_name_map" in context
        assert "prompts_count_map" in context
        assert "prompts" in context
        assert "user_custom_doc" in context
        assert "least_privileges" in context

    def test_build_retrieve_context_check_public_raises(self, fake_gateway, fake_stage):
        """check_public=True 且非公开非维护者时应抛出异常"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway._maintainers = "admin"
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=False,
        )

        with pytest.raises(Exception):
            MCPServerHandler.build_retrieve_context(mcp_server, check_public=True, username="other")

    def test_build_retrieve_context_inactive_raises(self, fake_gateway, fake_stage):
        """MCPServer 未启用时应抛出异常"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.INACTIVE.value,
            is_public=True,
        )

        with pytest.raises(Exception):
            MCPServerHandler.build_retrieve_context(mcp_server)

    # ========== save_mcp_servers 测试 ==========

    def test_save_mcp_servers_create(self, fake_gateway, fake_stage):
        """创建新的 MCP Server"""
        with patch.object(MCPServerHandler, "sync_permissions"):
            results = MCPServerHandler.save_mcp_servers(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                mcp_servers_data=[
                    {
                        "name": "server1",
                        "description": "test server",
                        "resource_names": ["res1"],
                        "tool_names": ["res1"],
                        "is_public": True,
                        "status": MCPServerStatusEnum.ACTIVE.value,
                    }
                ],
            )

        assert len(results) == 1
        assert results[0]["action"] == "created"
        assert results[0]["name"] == f"{fake_gateway.name}-{fake_stage.name}-server1"

        instance = MCPServer.objects.get(id=results[0]["id"])
        assert instance.description == "test server"
        assert instance.resource_names == ["res1"]

    def test_save_mcp_servers_update(self, fake_gateway, fake_stage):
        """更新已有的 MCP Server"""
        full_name = MCPServerHandler.get_mcp_server_name(
            gateway_name=fake_gateway.name, stage_name=fake_stage.name, name="server1"
        )
        existing = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name=full_name,
            description="old",
            status=MCPServerStatusEnum.INACTIVE.value,
        )

        with patch.object(MCPServerHandler, "sync_permissions"):
            results = MCPServerHandler.save_mcp_servers(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                mcp_servers_data=[
                    {
                        "name": "server1",
                        "description": "updated",
                        "resource_names": ["res1"],
                        "tool_names": ["res1"],
                        "is_public": True,
                        "status": MCPServerStatusEnum.ACTIVE.value,
                    }
                ],
            )

        assert len(results) == 1
        assert results[0]["action"] == "updated"
        assert results[0]["id"] == existing.id

        existing.refresh_from_db()
        assert existing.description == "updated"
        assert existing.status == MCPServerStatusEnum.ACTIVE.value

    def test_save_mcp_servers_with_permissions(self, fake_gateway, fake_stage):
        """创建时同步权限"""
        with patch.object(MCPServerHandler, "sync_permissions") as mock_sync:
            results = MCPServerHandler.save_mcp_servers(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                mcp_servers_data=[
                    {
                        "name": "server1",
                        "description": "test",
                        "resource_names": ["res1"],
                        "tool_names": ["res1"],
                        "is_public": True,
                        "status": MCPServerStatusEnum.ACTIVE.value,
                        "target_app_codes": ["app1", "app2"],
                    }
                ],
            )

        mcp_server_id = results[0]["id"]
        assert MCPServerAppPermission.objects.filter(mcp_server_id=mcp_server_id).count() == 2
        mock_sync.assert_called_once_with(mcp_server_id)

    def test_save_mcp_servers_with_categories(self, fake_gateway, fake_stage):
        """创建时同步分类"""
        MCPServerCategory.objects.get_or_create(name="Official", defaults={"display_name": "官方"})

        with patch.object(MCPServerHandler, "sync_permissions"):
            results = MCPServerHandler.save_mcp_servers(
                gateway_id=fake_gateway.id,
                gateway_name=fake_gateway.name,
                stage_id=fake_stage.id,
                stage_name=fake_stage.name,
                mcp_servers_data=[
                    {
                        "name": "server1",
                        "description": "test",
                        "resource_names": ["res1"],
                        "tool_names": ["res1"],
                        "is_public": True,
                        "status": MCPServerStatusEnum.ACTIVE.value,
                        "category_names": ["Official"],
                    }
                ],
            )

        instance = MCPServer.objects.get(id=results[0]["id"])
        assert list(instance.categories.values_list("name", flat=True)) == ["Official"]

    # ========== _sync_mcp_server_permissions 测试 ==========

    def test_sync_mcp_server_permissions(self, fake_gateway, fake_stage):
        """调用权限同步"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        with patch.object(MCPServerHandler, "sync_permissions") as mock_sync:
            MCPServerHandler._sync_mcp_server_permissions(mcp_server.id, ["app1", "app2"])

        assert MCPServerAppPermission.objects.filter(mcp_server_id=mcp_server.id).count() == 2
        mock_sync.assert_called_once_with(mcp_server.id)

    # ========== _sync_mcp_server_categories 测试 ==========

    def test_sync_mcp_server_categories_set(self, fake_gateway, fake_stage):
        """设置分类"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        MCPServerCategory.objects.get_or_create(name="Featured", defaults={"display_name": "精选"})

        MCPServerHandler._sync_mcp_server_categories(mcp_server, ["Featured"])

        assert list(mcp_server.categories.values_list("name", flat=True)) == ["Featured"]

    def test_sync_mcp_server_categories_clear(self, fake_gateway, fake_stage):
        """传空列表清除分类"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        cat, _ = MCPServerCategory.objects.get_or_create(name="Official", defaults={"display_name": "官方"})
        mcp_server.categories.add(cat)

        MCPServerHandler._sync_mcp_server_categories(mcp_server, [])

        assert mcp_server.categories.count() == 0

    def test_sync_mcp_server_categories_none_noop(self, fake_gateway, fake_stage):
        """传 None 不操作"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        cat, _ = MCPServerCategory.objects.get_or_create(name="Official", defaults={"display_name": "官方"})
        mcp_server.categories.add(cat)

        MCPServerHandler._sync_mcp_server_categories(mcp_server, None)

        assert mcp_server.categories.count() == 1

    def test_build_batch_agent_client_config_empty_list(self):
        """测试空列表返回空配置"""
        result = MCPServerHandler.build_batch_agent_client_config([], "cursor", {}, user_tenant_id="")
        assert result == {"mcpServers": {}}

    def test_build_batch_agent_client_config_cursor(self, fake_gateway, fake_stage):
        """测试批量生成 Cursor 配置"""
        server1 = G(
            MCPServer,
            name="server-1",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
        )
        server2 = G(
            MCPServer,
            name="server-2",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource2",
            oauth2_public_client_enabled=False,
        )

        least_privileges = {server1.id: "", server2.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server1, server2], "cursor", least_privileges, user_tenant_id=""
        )

        assert "mcpServers" in result
        assert "server-1" in result["mcpServers"]
        assert "server-2" in result["mcpServers"]

        # 验证 Cursor 配置结构（不带 type 字段）
        config1 = result["mcpServers"]["server-1"]
        assert "url" in config1
        assert "type" not in config1
        assert "headers" in config1
        assert "X-Bkapi-Authorization" in config1["headers"]

    def test_build_batch_agent_client_config_codebuddy(self, fake_gateway, fake_stage):
        """测试批量生成 CodeBuddy 配置（包含 transportType）"""
        server = G(
            MCPServer,
            name="codebuddy-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
            protocol_type="streamable_http",
        )

        least_privileges = {server.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server], "codebuddy", least_privileges, user_tenant_id=""
        )

        config = result["mcpServers"]["codebuddy-server"]
        assert "url" in config
        assert "transportType" in config
        assert config["transportType"] == "streamable-http"
        assert "type" not in config

    def test_build_batch_agent_client_config_claude(self, fake_gateway, fake_stage):
        """测试批量生成 Claude 配置（包含 type 字段，顶层 key 为 mcpServers）"""
        server = G(
            MCPServer,
            name="claude-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
            protocol_type="streamable_http",
        )

        least_privileges = {server.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server], "claude", least_privileges, user_tenant_id=""
        )

        # Claude 顶层 key 为 mcpServers
        assert "mcpServers" in result
        config = result["mcpServers"]["claude-server"]
        assert "url" in config
        assert "type" in config
        assert config["type"] == "http"
        assert "transportType" not in config

    def test_build_batch_agent_client_config_vscode(self, fake_gateway, fake_stage):
        """测试批量生成 VSCode 配置（包含 type 字段，顶层 key 为 servers）"""
        server = G(
            MCPServer,
            name="vscode-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
            protocol_type="streamable_http",
        )

        least_privileges = {server.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server], "vscode", least_privileges, user_tenant_id=""
        )

        # VSCode 顶层 key 为 servers
        assert "servers" in result
        assert "mcpServers" not in result
        config = result["servers"]["vscode-server"]
        assert "url" in config
        assert "type" in config
        assert config["type"] == "http"

    def test_build_batch_agent_client_config_oauth2_public_client_enabled(self, fake_gateway, fake_stage, settings):
        """测试 OAuth2 公开客户端模式开启时不包含认证请求头"""
        server = G(
            MCPServer,
            name="oauth2-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=True,
        )

        least_privileges = {server.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server], "cursor", least_privileges, user_tenant_id=""
        )

        config = result["mcpServers"]["oauth2-server"]
        # OAuth2 公开客户端模式下不应该有 headers
        assert "headers" not in config or "X-Bkapi-Authorization" not in config.get("headers", {})

    def test_build_batch_agent_client_config_with_tenant(self, fake_gateway, fake_stage, settings):
        """测试多租户模式下包含租户 ID"""
        settings.ENABLE_MULTI_TENANT_MODE = True

        server = G(
            MCPServer,
            name="tenant-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
        )

        least_privileges = {server.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server], "cursor", least_privileges, user_tenant_id="tenant-123"
        )

        config = result["mcpServers"]["tenant-server"]
        assert "headers" in config
        assert "X-Bk-Tenant-Id" in config["headers"]
        assert config["headers"]["X-Bk-Tenant-Id"] == "tenant-123"

    def test_build_batch_agent_client_config_sse_protocol(self, fake_gateway, fake_stage):
        """测试 SSE 协议类型"""
        server = G(
            MCPServer,
            name="sse-server",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
            protocol_type="sse",
        )

        least_privileges = {server.id: ""}

        result = MCPServerHandler.build_batch_agent_client_config(
            [server], "codebuddy", least_privileges, user_tenant_id=""
        )

        config = result["mcpServers"]["sse-server"]
        # SSE 协议下 CodeBuddy 的 transportType 应为 sse
        assert config["transportType"] == "sse"

    def test_build_batch_agent_client_config_per_server_least_privilege(self, fake_gateway, fake_stage):
        """测试同一 gateway+stage 下不同 server 的 least_privilege 独立计算"""
        server1 = G(
            MCPServer,
            name="server-app",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource1",
            oauth2_public_client_enabled=False,
        )
        server2 = G(
            MCPServer,
            name="server-user",
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            _resource_names="resource2",
            oauth2_public_client_enabled=False,
        )

        # 不同的 least_privilege（按 mcp_server.id 为 key）
        least_privileges = {
            server1.id: MCPServerLeastPrivilegeEnum.APPLICATION.value,
            server2.id: MCPServerLeastPrivilegeEnum.APPLICATION_AND_USER.value,
        }

        result = MCPServerHandler.build_batch_agent_client_config(
            [server1, server2], "cursor", least_privileges, user_tenant_id=""
        )

        assert "server-app" in result["mcpServers"]
        assert "server-user" in result["mcpServers"]
