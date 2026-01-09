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
from apigateway.apps.mcp_server.models import (
    TOOL_NAME_SEPARATOR,
    MCPServer,
)


class TestToolNameSeparator:
    """测试 TOOL_NAME_SEPARATOR 常量"""

    def test_separator_value(self):
        """测试分隔符值"""
        assert TOOL_NAME_SEPARATOR == "@"


class TestMCPServer:
    def test_labels(self):
        mcp_server = G(MCPServer)
        assert mcp_server.labels == []

        mcp_server.labels = ["label1", "label2"]
        assert mcp_server.labels == ["label1", "label2"]

    def test_is_active(self):
        mcp_server = G(MCPServer)
        assert mcp_server.is_active is False

        mcp_server.status = MCPServerStatusEnum.ACTIVE.value
        assert mcp_server.is_active is True

    def test_parse_resource_names_to_part(self):
        mcp_server = G(MCPServer)
        assert mcp_server._parse_resource_names_to_part(0) == []
        assert mcp_server._parse_resource_names_to_part(1) == []

        mcp_server._resource_names = "resource1;resource2;resource3"
        assert mcp_server._parse_resource_names_to_part(0) == ["resource1", "resource2", "resource3"]
        assert mcp_server._parse_resource_names_to_part(1) == ["resource1", "resource2", "resource3"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3@tool3"
        assert mcp_server._parse_resource_names_to_part(0) == ["resource1", "resource2", "resource3"]
        assert mcp_server._parse_resource_names_to_part(1) == ["tool1", "tool2", "tool3"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3"
        assert mcp_server._parse_resource_names_to_part(0) == ["resource1", "resource2", "resource3"]
        assert mcp_server._parse_resource_names_to_part(1) == ["tool1", "tool2", "resource3"]

    def test_resource_names(self):
        mcp_server = G(MCPServer)
        assert mcp_server.resource_names == []

        mcp_server._resource_names = "resource1;resource2"
        assert mcp_server.resource_names == ["resource1", "resource2"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3"
        assert mcp_server.resource_names == ["resource1", "resource2", "resource3"]

    def test_resource_names_setter(self):
        mcp_server = G(MCPServer)
        with pytest.raises(NotImplementedError):
            mcp_server.resource_names = ["resource1", "resource2"]

    def test_delete_resource_names(self):
        mcp_server = G(MCPServer)
        assert not mcp_server.delete_resource_names(set())

        mcp_server._resource_names = "resource1;resource2;resource3"
        assert mcp_server.delete_resource_names({"resource1", "resource2"})
        assert mcp_server.resource_names == ["resource3"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3@tool3"
        assert mcp_server.delete_resource_names({"resource1", "resource3"})
        assert mcp_server.resource_names == ["resource2"]

    def test_tool_names(self):
        mcp_server = G(MCPServer)
        assert mcp_server.tool_names == []

        mcp_server._resource_names = "resource1;resource2"
        assert mcp_server.tool_names == ["resource1", "resource2"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3@tool3"
        assert mcp_server.tool_names == ["tool1", "tool2", "tool3"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3"
        assert mcp_server.tool_names == ["tool1", "tool2", "resource3"]

    def test_tool_names_setter(self):
        mcp_server = G(MCPServer)
        with pytest.raises(NotImplementedError):
            mcp_server.tool_names = ["tool1", "tool2"]

    def test_tools_count(self):
        """测试不带工具名的 tools_count"""
        mcp_server = G(MCPServer)
        assert mcp_server.tools_count == 0

        mcp_server._resource_names = "resource1;resource2"
        assert mcp_server.tools_count == 2

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3@tool3"
        assert mcp_server.tools_count == 3

    def test_update_resource_names(self):
        mcp_server = G(MCPServer)
        with pytest.raises(ValueError):
            mcp_server.update_resource_names(["resource1", "resource2"], ["tool1"])

        mcp_server._resource_names = "resource1;resource2;resource3"
        mcp_server.update_resource_names(["resource1", "resource2", "resource4"], ["tool1", "tool2", "tool4"])
        assert mcp_server.resource_names == ["resource1", "resource2", "resource4"]
        assert mcp_server.tool_names == ["tool1", "tool2", "tool4"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3@tool3"
        mcp_server.update_resource_names(["resource1", "resource2", "resource4"], ["tool11", "tool22", "tool44"])
        assert mcp_server.resource_names == ["resource1", "resource2", "resource4"]
        assert mcp_server.tool_names == ["tool11", "tool22", "tool44"]

        mcp_server._resource_names = "resource1@tool1;resource2@tool2;resource3"
        mcp_server.update_resource_names(
            ["resource1", "resource2", "resource4"], ["resource1", "resource2", "resource4"]
        )
        assert mcp_server.resource_names == ["resource1", "resource2", "resource4"]
        assert mcp_server.tool_names == ["resource1", "resource2", "resource4"]
