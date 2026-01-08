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
from apigateway.apps.mcp_server.models import MCPServer
from apigateway.common.constants import CallSourceTypeEnum

pytestmark = pytest.mark.django_db


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
        # 验证返回原始格式（由 model 层处理转换）
        assert slz.validated_data["resource_names"] == [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
        ]

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

    def test_validate_resource_names_duplicate_resource_name(self, fake_gateway, fake_stage):
        """测试重复的 resource_name"""
        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": [
                {"resource_name": "resource1", "tool_name": "tool1"},
                {"resource_name": "resource1", "tool_name": "tool2"},
            ],
        }
        slz = MCPServerCreateInputSLZ(data=data, context={"gateway": fake_gateway, "source": CallSourceTypeEnum.Web})
        assert not slz.is_valid()
        assert "resource_names" in slz.errors
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
        # 验证返回原始格式（由 model 层处理转换）
        assert slz.validated_data["resource_names"] == [
            {"resource_name": "resource1", "tool_name": ""},
            {"resource_name": "resource2", "tool_name": ""},
            {"resource_name": "resource3", "tool_name": ""},
        ]


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
        # 验证返回原始格式（由 model 层处理转换）
        assert slz.validated_data["resource_names"] == [
            {"resource_name": "resource1", "tool_name": "custom_tool"},
            {"resource_name": "resource2", "tool_name": ""},
        ]

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

    def test_validate_resource_names_duplicate_resource_name(self, fake_gateway, fake_stage):
        """测试重复的 resource_name"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": [
                {"resource_name": "resource1", "tool_name": "tool1"},
                {"resource_name": "resource1", "tool_name": "tool2"},
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
        # 验证返回原始格式（由 model 层处理转换）
        assert slz.validated_data["resource_names"] == [
            {"resource_name": "resource1", "tool_name": ""},
            {"resource_name": "resource2", "tool_name": ""},
        ]

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
