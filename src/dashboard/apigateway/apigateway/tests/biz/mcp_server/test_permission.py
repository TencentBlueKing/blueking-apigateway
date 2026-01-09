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

from unittest.mock import patch

from ddf import G

from apigateway.apps.mcp_server.models import MCPServer, MCPServerAppPermission
from apigateway.apps.permission.constants import GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.biz.mcp_server import MCPServerHandler
from apigateway.core.models import Resource
from apigateway.utils.time import NeverExpiresTime


class TestMCPServerPermissionHandler:
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
