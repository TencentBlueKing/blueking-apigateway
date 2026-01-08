# -*- coding: utf-8 -*-
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

import pytest
from ddf import G

from apigateway.apis.web.mcp_server.serializers import (
    MCPServerCreateInputSLZ,
    MCPServerResourceNameInputItemSLZ,
    MCPServerUpdateInputSLZ,
)
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import (
    MCPServer,
    convert_resource_names_from_storage_format,
    convert_resource_names_to_storage_format,
    get_pure_resource_names,
    get_resource_name_tool_map,
    parse_resource_name_with_tool,
)
from apigateway.common.constants import CallSourceTypeEnum

pytestmark = pytest.mark.django_db


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


class TestMCPServerResourceNameInputItemSLZ:
    """测试 MCPServerResourceNameInputItemSLZ 序列化器"""

    def test_valid_with_tool_name(self):
        """测试带 tool_name 的有效数据"""
        slz = MCPServerResourceNameInputItemSLZ(data={"resource_name": "test_resource", "tool_name": "custom_tool"})
        assert slz.is_valid()
        assert slz.validated_data["resource_name"] == "test_resource"
        assert slz.validated_data["tool_name"] == "custom_tool"

    def test_valid_without_tool_name(self):
        """测试不带 tool_name 的有效数据"""
        slz = MCPServerResourceNameInputItemSLZ(data={"resource_name": "test_resource"})
        assert slz.is_valid()
        assert slz.validated_data["resource_name"] == "test_resource"
        assert slz.validated_data["tool_name"] == ""

    def test_valid_with_empty_tool_name(self):
        """测试 tool_name 为空字符串的情况"""
        slz = MCPServerResourceNameInputItemSLZ(data={"resource_name": "test_resource", "tool_name": ""})
        assert slz.is_valid()
        assert slz.validated_data["tool_name"] == ""

    def test_invalid_missing_resource_name(self):
        """测试缺少 resource_name 的情况"""
        slz = MCPServerResourceNameInputItemSLZ(data={"tool_name": "custom_tool"})
        assert not slz.is_valid()
        assert "resource_name" in slz.errors


class TestMCPServerCreateInputSLZ:
    """测试 MCPServerCreateInputSLZ 序列化器"""

    def test_validate_resource_names_empty(self, fake_gateway, fake_stage):
        """测试空资源名称列表"""
        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": [],
        }
        slz = MCPServerCreateInputSLZ(data=data, context={"gateway": fake_gateway, "source": CallSourceTypeEnum.Web})
        assert not slz.is_valid()
        assert "resource_names" in slz.errors

    @patch("apigateway.biz.validators.MCPServerHandler.get_valid_resource_names")
    def test_validate_resource_names_with_tool_name(self, mock_get_valid, fake_gateway, fake_stage):
        """测试带 tool_name 的资源名称列表"""
        mock_get_valid.return_value = {"resource1", "resource2"}

        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": [
                {"resource_name": "resource1", "tool_name": "custom_tool"},
                {"resource_name": "resource2", "tool_name": ""},
            ],
        }
        slz = MCPServerCreateInputSLZ(data=data, context={"gateway": fake_gateway, "source": CallSourceTypeEnum.Web})
        assert slz.is_valid(), slz.errors
        # 验证转换后的格式
        assert slz.validated_data["resource_names"] == ["resource1@custom_tool", "resource2"]

    def test_validate_resource_names_duplicate_tool_name(self, fake_gateway, fake_stage):
        """测试重复的 tool_name"""
        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": [
                {"resource_name": "resource1", "tool_name": "same_tool"},
                {"resource_name": "resource2", "tool_name": "same_tool"},
            ],
        }
        slz = MCPServerCreateInputSLZ(data=data, context={"gateway": fake_gateway, "source": CallSourceTypeEnum.Web})
        assert not slz.is_valid()
        assert "resource_names" in slz.errors
        # 验证错误信息包含重复提示
        error_msg = str(slz.errors["resource_names"])
        assert "重复" in error_msg

    @patch("apigateway.biz.validators.MCPServerHandler.get_valid_resource_names")
    def test_validate_resource_names_empty_tool_names_not_duplicate(self, mock_get_valid, fake_gateway, fake_stage):
        """测试多个空 tool_name 不算重复"""
        mock_get_valid.return_value = {"resource1", "resource2", "resource3"}

        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": [
                {"resource_name": "resource1", "tool_name": ""},
                {"resource_name": "resource2", "tool_name": ""},
                {"resource_name": "resource3"},
            ],
        }
        slz = MCPServerCreateInputSLZ(data=data, context={"gateway": fake_gateway, "source": CallSourceTypeEnum.Web})
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["resource_names"] == ["resource1", "resource2", "resource3"]


class TestMCPServerUpdateInputSLZ:
    """测试 MCPServerUpdateInputSLZ 序列化器"""

    def test_validate_resource_names_empty(self, fake_gateway, fake_stage):
        """测试空资源名称列表"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": [],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert not slz.is_valid()
        assert "resource_names" in slz.errors

    def test_validate_resource_names_invalid_resource(self, fake_gateway, fake_stage):
        """测试无效的资源名称"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": [
                {"resource_name": "invalid_resource", "tool_name": ""},
            ],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert not slz.is_valid()
        assert "resource_names" in slz.errors

    def test_validate_resource_names_with_tool_name(self, fake_gateway, fake_stage):
        """测试带 tool_name 的资源名称列表"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": [
                {"resource_name": "resource1", "tool_name": "custom_tool"},
                {"resource_name": "resource2", "tool_name": ""},
            ],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["resource_names"] == ["resource1@custom_tool", "resource2"]

    def test_validate_resource_names_duplicate_tool_name(self, fake_gateway, fake_stage):
        """测试重复的 tool_name"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": [
                {"resource_name": "resource1", "tool_name": "same_tool"},
                {"resource_name": "resource2", "tool_name": "same_tool"},
            ],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert not slz.is_valid()
        assert "resource_names" in slz.errors
        error_msg = str(slz.errors["resource_names"])
        assert "重复" in error_msg

    def test_validate_resource_names_empty_tool_names_not_duplicate(self, fake_gateway, fake_stage):
        """测试多个空 tool_name 不算重复"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": [
                {"resource_name": "resource1", "tool_name": ""},
                {"resource_name": "resource2"},
            ],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["resource_names"] == ["resource1", "resource2"]

    def test_validate_resource_names_none(self, fake_gateway, fake_stage):
        """测试 resource_names 为 None（不更新）"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        assert "resource_names" not in slz.validated_data


class TestMCPServerModelResourceNames:
    """测试 MCPServer model 中 resource_names 相关属性"""

    def test_resource_names_with_tool_getter(self, fake_gateway, fake_stage):
        """测试 resource_names_with_tool getter"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        # 设置存储格式的资源名称（使用 resource_names_raw）
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2"]
        mcp_server.save()

        # 验证 resource_names_with_tool 返回正确格式
        assert mcp_server.resource_names_with_tool == [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
        ]

    def test_resource_names_with_tool_setter(self, fake_gateway, fake_stage):
        """测试 resource_names_with_tool setter"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        # 使用前端格式设置资源名称
        mcp_server.resource_names_with_tool = [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
        ]
        mcp_server.save()

        # 验证存储格式正确（使用 resource_names_raw 检查）
        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2"]
        # resource_names 返回纯资源名称
        assert mcp_server.resource_names == ["resource1", "resource2"]

    def test_resource_names_returns_pure_names(self, fake_gateway, fake_stage):
        """测试 resource_names 返回纯资源名称（向后兼容）"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2", "resource3@tool3"]
        mcp_server.save()

        # 验证 resource_names 返回纯资源名称
        assert mcp_server.resource_names == ["resource1", "resource2", "resource3"]
        # 验证 resource_names_raw 返回完整存储格式
        assert mcp_server.resource_names_raw == ["resource1@custom_tool", "resource2", "resource3@tool3"]

    def test_resource_name_tool_map(self, fake_gateway, fake_stage):
        """测试 resource_name_tool_map 属性"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server.resource_names_raw = ["resource1@custom_tool", "resource2", "resource3@tool3"]
        mcp_server.save()

        # 验证资源名到工具名的映射
        assert mcp_server.resource_name_tool_map == {
            "resource1": "custom_tool",
            "resource2": "",
            "resource3": "tool3",
        }

    def test_empty_resource_names(self, fake_gateway, fake_stage):
        """测试空资源名称列表"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
        )
        mcp_server._resource_names = ""
        mcp_server.save()

        assert mcp_server.resource_names == []
        assert mcp_server.resource_names_raw == []
        assert mcp_server.resource_names_with_tool == []
        assert mcp_server.resource_name_tool_map == {}
