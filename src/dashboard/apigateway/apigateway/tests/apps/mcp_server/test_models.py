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

from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import (
    TOOL_NAME_SEPARATOR,
    MCPServer,
    convert_resource_names_from_storage_format,
    convert_resource_names_to_storage_format,
    get_pure_resource_names,
    get_resource_name_tool_map,
    parse_resource_name_with_tool,
)


class TestParseResourceNameWithTool:
    """测试 parse_resource_name_with_tool 函数"""

    def test_without_tool_name(self):
        """测试不带工具名的资源名称"""
        resource_name, tool_name = parse_resource_name_with_tool("resource1")
        assert resource_name == "resource1"
        assert tool_name == ""

    def test_with_tool_name(self):
        """测试带工具名的资源名称"""
        resource_name, tool_name = parse_resource_name_with_tool("resource1@custom_tool")
        assert resource_name == "resource1"
        assert tool_name == "custom_tool"

    def test_with_multiple_separators(self):
        """测试包含多个分隔符的情况（只分割第一个）"""
        resource_name, tool_name = parse_resource_name_with_tool("resource1@tool@extra")
        assert resource_name == "resource1"
        assert tool_name == "tool@extra"

    def test_empty_string(self):
        """测试空字符串"""
        resource_name, tool_name = parse_resource_name_with_tool("")
        assert resource_name == ""
        assert tool_name == ""

    def test_only_separator(self):
        """测试只有分隔符"""
        resource_name, tool_name = parse_resource_name_with_tool("@")
        assert resource_name == ""
        assert tool_name == ""

    def test_separator_at_end(self):
        """测试分隔符在末尾"""
        resource_name, tool_name = parse_resource_name_with_tool("resource1@")
        assert resource_name == "resource1"
        assert tool_name == ""


class TestConvertResourceNamesToStorageFormat:
    """测试 convert_resource_names_to_storage_format 函数"""

    def test_without_tool_name(self):
        """测试不带 tool_name 的情况"""
        resource_names = [
            {"resource_name": "resource1", "tool_name": ""},
            {"resource_name": "resource2"},
        ]
        result = convert_resource_names_to_storage_format(resource_names)
        assert result == ["resource1", "resource2"]

    def test_with_tool_name(self):
        """测试带 tool_name 的情况"""
        resource_names = [
            {"resource_name": "resource1", "tool_name": "custom_tool1"},
            {"resource_name": "resource2", "tool_name": "custom_tool2"},
        ]
        result = convert_resource_names_to_storage_format(resource_names)
        assert result == ["resource1@custom_tool1", "resource2@custom_tool2"]

    def test_mixed(self):
        """测试混合情况"""
        resource_names = [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
            {"resource_name": "resource3"},
        ]
        result = convert_resource_names_to_storage_format(resource_names)
        assert result == ["resource1@custom_tool", "resource2", "resource3"]

    def test_empty_list(self):
        """测试空列表"""
        result = convert_resource_names_to_storage_format([])
        assert result == []


class TestConvertResourceNamesFromStorageFormat:
    """测试 convert_resource_names_from_storage_format 函数"""

    def test_without_tool_name(self):
        """测试不带工具名的存储格式"""
        resource_names = ["resource1", "resource2"]
        result = convert_resource_names_from_storage_format(resource_names)
        assert result == [
            {"resource_name": "resource1", "tool_name": ""},
            {"resource_name": "resource2", "tool_name": ""},
        ]

    def test_with_tool_name(self):
        """测试带工具名的存储格式"""
        resource_names = ["resource1@custom_tool1", "resource2@custom_tool2"]
        result = convert_resource_names_from_storage_format(resource_names)
        assert result == [
            {"resource_name": "resource1", "tool_name": "custom_tool1"},
            {"resource_name": "resource2", "tool_name": "custom_tool2"},
        ]

    def test_mixed(self):
        """测试混合情况"""
        resource_names = ["resource1@custom_tool", "resource2", "resource3@tool3"]
        result = convert_resource_names_from_storage_format(resource_names)
        assert result == [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
            {"resource_name": "resource3", "tool_name": "tool3"},
        ]

    def test_empty_list(self):
        """测试空列表"""
        result = convert_resource_names_from_storage_format([])
        assert result == []


class TestGetPureResourceNames:
    """测试 get_pure_resource_names 函数"""

    def test_without_tool_name(self):
        """测试不带工具名的资源名称"""
        resource_names = ["resource1", "resource2"]
        result = get_pure_resource_names(resource_names)
        assert result == ["resource1", "resource2"]

    def test_with_tool_name(self):
        """测试带工具名的资源名称"""
        resource_names = ["resource1@custom_tool1", "resource2@custom_tool2"]
        result = get_pure_resource_names(resource_names)
        assert result == ["resource1", "resource2"]

    def test_mixed(self):
        """测试混合情况"""
        resource_names = ["resource1@custom_tool", "resource2", "resource3@tool3"]
        result = get_pure_resource_names(resource_names)
        assert result == ["resource1", "resource2", "resource3"]

    def test_empty_list(self):
        """测试空列表"""
        result = get_pure_resource_names([])
        assert result == []


class TestGetResourceNameToolMap:
    """测试 get_resource_name_tool_map 函数"""

    def test_without_tool_name(self):
        """测试不带工具名的资源名称"""
        resource_names = ["resource1", "resource2"]
        result = get_resource_name_tool_map(resource_names)
        assert result == {"resource1": "", "resource2": ""}

    def test_with_tool_name(self):
        """测试带工具名的资源名称"""
        resource_names = ["resource1@custom_tool1", "resource2@custom_tool2"]
        result = get_resource_name_tool_map(resource_names)
        assert result == {"resource1": "custom_tool1", "resource2": "custom_tool2"}

    def test_mixed(self):
        """测试混合情况"""
        resource_names = ["resource1@custom_tool", "resource2", "resource3@tool3"]
        result = get_resource_name_tool_map(resource_names)
        assert result == {"resource1": "custom_tool", "resource2": "", "resource3": "tool3"}

    def test_empty_list(self):
        """测试空列表"""
        result = get_resource_name_tool_map([])
        assert result == {}


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

    def test_resource_names_without_tool(self):
        """测试不带工具名的 resource_names"""
        mcp_server = G(MCPServer)
        assert mcp_server.resource_names == []

        mcp_server.resource_names = ["resource1", "resource2"]
        assert mcp_server.resource_names == ["resource1", "resource2"]

    def test_resource_names_with_tool(self):
        """测试带工具名的 resource_names（返回纯资源名称）"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names = ["resource1@custom_tool", "resource2"]

        # resource_names 返回纯资源名称
        assert mcp_server.resource_names == ["resource1", "resource2"]

    def test_resource_names_raw(self):
        """测试 resource_names_raw 属性"""
        mcp_server = G(MCPServer)
        assert mcp_server.resource_names_raw == []

        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]
        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2"]

    def test_resource_names_with_tool_property(self):
        """测试 resource_names_with_tool 属性"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]

        assert mcp_server.resource_names_with_tool == [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
        ]

    def test_resource_names_with_tool_setter(self):
        """测试 resource_names_with_tool setter"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_with_tool = [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
        ]

        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2"]
        assert mcp_server.resource_names == ["resource1", "resource2"]

    def test_resource_name_tool_map(self):
        """测试 resource_name_tool_map 属性"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2", "resource3@tool3"]

        assert mcp_server.resource_name_tool_map == {
            "resource1": "custom_tool",
            "resource2": "",
            "resource3": "tool3",
        }

    def test_is_active(self):
        mcp_server = G(MCPServer)
        assert mcp_server.is_active is False

        mcp_server.status = MCPServerStatusEnum.ACTIVE.value
        assert mcp_server.is_active is True

    def test_tools_count_without_tool_name(self):
        """测试不带工具名的 tools_count"""
        mcp_server = G(MCPServer)
        assert mcp_server.tools_count == 0

        mcp_server.resource_names = ["resource1", "resource2"]
        assert mcp_server.tools_count == 2

    def test_tools_count_with_tool_name(self):
        """测试带工具名的 tools_count"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]
        assert mcp_server.tools_count == 2

    def test_empty_resource_names(self):
        """测试空资源名称的各种属性"""
        mcp_server = G(MCPServer)
        mcp_server._resource_names = ""

        assert mcp_server.resource_names == []
        assert mcp_server.resource_names_raw == []
        assert mcp_server.resource_names_with_tool == []
        assert mcp_server.resource_name_tool_map == {}
        assert mcp_server.tools_count == 0

    def test_tool_names_property(self):
        """测试 tool_names 属性"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2", "resource3@tool3"]

        assert mcp_server.tool_names == ["custom_tool", "", "tool3"]

    def test_tool_names_empty(self):
        """测试空资源时的 tool_names"""
        mcp_server = G(MCPServer)
        mcp_server._resource_names = ""

        assert mcp_server.tool_names == []

    def test_update_resource_names(self):
        """测试 update_resource_names 方法"""
        mcp_server = G(MCPServer)
        mcp_server.update_resource_names(
            [
                {"resource_name": "resource1", "tool_name": "custom_tool"},
                {"resource_name": "resource2", "tool_name": ""},
            ]
        )

        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2"]
        assert mcp_server.resource_names == ["resource1", "resource2"]

    def test_remove_deleted_resources_some_deleted(self):
        """测试 remove_deleted_resources 方法 - 部分删除"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2", "resource3@tool3"]

        result = mcp_server.remove_deleted_resources({"resource2"})

        assert result is True
        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource3@tool3"]
        assert mcp_server.resource_names == ["resource1", "resource3"]

    def test_remove_deleted_resources_all_deleted(self):
        """测试 remove_deleted_resources 方法 - 全部删除"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]

        result = mcp_server.remove_deleted_resources({"resource1", "resource2"})

        assert result is True
        assert mcp_server.resource_names_raw == []
        assert mcp_server.resource_names == []

    def test_remove_deleted_resources_none_deleted(self):
        """测试 remove_deleted_resources 方法 - 无删除"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]

        result = mcp_server.remove_deleted_resources({"resource3", "resource4"})

        assert result is False
        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2"]

    def test_remove_deleted_resources_empty_set(self):
        """测试 remove_deleted_resources 方法 - 空集合"""
        mcp_server = G(MCPServer)
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]

        result = mcp_server.remove_deleted_resources(set())

        assert result is False
        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2"]
