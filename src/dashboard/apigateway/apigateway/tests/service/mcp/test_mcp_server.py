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


import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.core.models import Gateway, ResourceVersion, Stage
from apigateway.service.mcp.mcp_server import (
    build_mcp_server_permission_approval_url,
    build_mcp_server_url,
    update_stage_mcp_server_related_resource_names,
)


class TestUpdateStageMcpServerRelatedResourceNames:
    """Test cases for update_stage_mcp_server_related_resource_names function"""

    @pytest.fixture
    def gateway(self):
        """Create a test gateway"""
        return G(Gateway)

    @pytest.fixture
    def stage(self, gateway):
        """Create a test stage"""
        return G(Stage, gateway=gateway)

    @pytest.fixture
    def resource_version(self, gateway):
        """Create a test resource version with sample data"""
        resource_version = G(ResourceVersion, gateway=gateway)
        resource_version.data = [
            {"name": "resource1", "method": "GET", "path": "/api/v1/resource1"},
            {"name": "resource2", "method": "POST", "path": "/api/v1/resource2"},
            {"name": "resource3", "method": "PUT", "path": "/api/v1/resource3"},
        ]
        resource_version.save()
        return resource_version

    def test_no_mcp_servers_for_stage(self, stage):
        """Test when there are no MCP servers for the stage"""
        # Call the function
        update_stage_mcp_server_related_resource_names(stage.id, 999)

        # Should do nothing and not raise any errors
        assert MCPServer.objects.filter(stage_id=stage.id).count() == 0

    def test_resource_version_not_found(self, stage):
        """Test when resource version doesn't exist"""
        # Create MCP servers for the stage
        mcp_server1 = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server1.resource_names = ["resource1", "resource2", "old_resource"]
        mcp_server1.save()

        mcp_server2 = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server2.resource_names = ["resource3", "another_old_resource"]
        mcp_server2.save()

        # Call function with non-existent resource version ID
        update_stage_mcp_server_related_resource_names(stage.id, 999999)

        # All resource names should be removed since resource version doesn't exist
        mcp_server1.refresh_from_db()
        mcp_server2.refresh_from_db()

        assert mcp_server1.resource_names == []
        assert mcp_server2.resource_names == []

    def test_no_deleted_resources(self, stage, resource_version):
        """Test when no resources are deleted (all MCP server resources exist in resource version)"""
        # Create MCP server with resources that all exist in resource version
        mcp_server = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server._resource_names = "resource1;resource2"
        mcp_server.save()

        original_resource_names = mcp_server.resource_names.copy()

        # Call the function
        update_stage_mcp_server_related_resource_names(stage.id, resource_version.id)

        # Resource names should remain unchanged
        mcp_server.refresh_from_db()
        assert mcp_server.resource_names == original_resource_names

    def test_some_resources_deleted(self, stage, resource_version):
        """Test when some resources are deleted from resource version"""
        # Create MCP server with mix of existing and deleted resources
        mcp_server = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server._resource_names = "resource1;deleted_resource1;resource2;deleted_resource2"
        mcp_server.save()

        # Call the function
        update_stage_mcp_server_related_resource_names(stage.id, resource_version.id)

        # Only existing resources should remain
        mcp_server.refresh_from_db()
        assert set(mcp_server.resource_names) == {"resource1", "resource2"}

    def test_all_resources_deleted(self, stage, resource_version):
        """Test when all MCP server resources are deleted from resource version"""
        # Create MCP server with only deleted resources
        mcp_server = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server._resource_names = "deleted_resource1;deleted_resource2;deleted_resource3"
        mcp_server.save()

        # Call the function
        update_stage_mcp_server_related_resource_names(stage.id, resource_version.id)

        # All resources should be removed
        mcp_server.refresh_from_db()
        assert mcp_server.resource_names == []

    def test_multiple_mcp_servers_mixed_scenarios(self, stage, resource_version):
        """Test with multiple MCP servers having different scenarios"""
        # MCP server 1: has some deleted resources
        mcp_server1 = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server1.resource_names = ["resource1", "deleted_resource1", "resource2"]
        mcp_server1.save()

        # MCP server 2: has no deleted resources
        mcp_server2 = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server2.resource_names = ["resource1", "resource3"]
        mcp_server2.save()

        # MCP server 3: has all deleted resources
        mcp_server3 = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server3.resource_names = ["deleted_resource1", "deleted_resource2"]
        mcp_server3.save()

        # MCP server 4: has no resources
        mcp_server4 = G(
            MCPServer,
            stage=stage,
            gateway=stage.gateway,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server4.resource_names = []
        mcp_server4.save()

        # Call the function
        update_stage_mcp_server_related_resource_names(stage.id, resource_version.id)

        # Check results
        mcp_server1.refresh_from_db()
        mcp_server2.refresh_from_db()
        mcp_server3.refresh_from_db()
        mcp_server4.refresh_from_db()

        assert set(mcp_server1.resource_names) == {"resource1", "resource2"}
        assert set(mcp_server2.resource_names) == {"resource1", "resource3"}  # unchanged
        assert mcp_server3.resource_names == []
        assert mcp_server4.resource_names == []  # unchanged


class TestBuildMCPServerURL:
    def test_build_mcp_server_url(self, settings):
        settings.BK_API_URL_TMPL = "http://test.com/{api_name}"

        url = build_mcp_server_url("test-mcp-server")
        assert url == "http://test.com/bk-apigateway/prod/api/v2/mcp-servers/test-mcp-server/sse/"


class TestBuildMCPServerPermissionApprovalURL:
    def test_build_mcp_server_permission_approval_url(self, settings):
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://dashboard.example.com/{gateway_id}/mcp/permission?serverId={mcp_server_id}"
        )

        url = build_mcp_server_permission_approval_url(gateway_id=123, mcp_server_id=456)
        assert url == "http://dashboard.example.com/123/mcp/permission?serverId=456"

    def test_build_mcp_server_permission_approval_url_with_different_ids(self, settings):
        settings.BK_MCP_SERVER_PERMISSION_APPROVAL_URL_TMPL = (
            "http://test.com/{gateway_id}/mcp/permission?serverId={mcp_server_id}"
        )

        url = build_mcp_server_permission_approval_url(gateway_id=1, mcp_server_id=2)
        assert url == "http://test.com/1/mcp/permission?serverId=2"
