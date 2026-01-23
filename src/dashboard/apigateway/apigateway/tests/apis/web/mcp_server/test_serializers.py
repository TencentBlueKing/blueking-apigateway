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
from uuid import uuid4

import pytest
from ddf import G

from apigateway.apis.web.mcp_server.serializers import (
    MCPServerCategoryOutputSLZ,
    MCPServerCreateInputSLZ,
    MCPServerListInputSLZ,
    MCPServerUpdateInputSLZ,
)
from apigateway.apps.mcp_server.constants import MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerCategory
from apigateway.common.constants import CallSourceTypeEnum, LanguageCodeEnum

pytestmark = pytest.mark.django_db


class TestMCPServerCategoryOutputSLZ:
    """测试 MCPServerCategoryOutputSLZ 序列化器的国际化功能"""

    @patch("apigateway.apis.web.mcp_server.serializers.get_current_language_code")
    def test_display_name_returns_name_for_english(self, mock_get_language):
        """测试英文环境返回 name"""
        mock_get_language.return_value = LanguageCodeEnum.EN.value
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category)
        assert slz.data["display_name"] == category.name
        assert slz.data["name"] == category.name

    @patch("apigateway.apis.web.mcp_server.serializers.get_current_language_code")
    def test_display_name_returns_display_name_for_chinese(self, mock_get_language):
        """测试中文环境返回 display_name"""
        mock_get_language.return_value = LanguageCodeEnum.ZH_HANS.value
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category)
        assert slz.data["display_name"] == "开发运维"
        assert slz.data["name"] == category.name

    @patch("apigateway.apis.web.mcp_server.serializers.get_current_language_code")
    def test_display_name_returns_display_name_for_other_languages(self, mock_get_language):
        """测试其他语言环境返回 display_name"""
        mock_get_language.return_value = "zh-hant"  # 繁体中文
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category)
        assert slz.data["display_name"] == "开发运维"


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
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }

        slz = MCPServerCreateInputSLZ(data=data, context=context)
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
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["custom_tool", "resource2"],
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }
        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["resource_names"] == ["resource1", "resource2"]
        assert slz.validated_data["tool_names"] == ["custom_tool", "resource2"]

    def test_validate_resource_names_duplicate_resource_name(self, fake_gateway, fake_stage):
        """测试重复的 resource_name"""
        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["resource1", "resource1"],
            "tool_names": ["tool1", "tool2"],
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }
        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert not slz.is_valid()
        assert "resource_names" in slz.errors
        error_msg = str(slz.errors["resource_names"])
        assert "重复" in error_msg

    def test_validate_tool_names_duplicate_tool_name(self, fake_gateway, fake_stage):
        """测试重复的 tool_name"""
        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["same_tool", "same_tool"],
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }
        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert not slz.is_valid()
        assert "tool_names" in slz.errors
        # 验证错误信息包含重复提示
        error_msg = str(slz.errors["tool_names"])
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
            "resource_names": ["resource1", "resource2", "resource3"],
            "tool_names": ["resource1", "resource2", "resource3"],
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2", "resource3"},
        }
        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["resource_names"] == ["resource1", "resource2", "resource3"]
        assert slz.validated_data["tool_names"] == ["resource1", "resource2", "resource3"]


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
            "resource_names": ["invalid_resource"],
            "tool_names": ["invalid_resource"],
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
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["custom_tool", "resource2"],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        # 验证返回原始格式（由 model 层处理转换）
        assert slz.validated_data["resource_names"] == ["resource1", "resource2"]
        assert slz.validated_data["tool_names"] == ["custom_tool", "resource2"]

    def test_validate_tool_names_duplicate_tool_name(self, fake_gateway, fake_stage):
        """测试重复的 tool_name"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["same_tool", "same_tool"],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert not slz.is_valid()
        assert "tool_names" in slz.errors
        error_msg = str(slz.errors["tool_names"])
        assert "重复" in error_msg

    def test_validate_resource_names_duplicate_resource_name(self, fake_gateway, fake_stage):
        """测试重复的 resource_name"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": ["resource1", "resource1"],
            "tool_names": ["tool1", "tool2"],
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
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        # 验证返回原始格式（由 model 层处理转换）
        assert slz.validated_data["resource_names"] == ["resource1", "resource2"]
        assert slz.validated_data["tool_names"] == ["resource1", "resource2"]

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


class TestMCPServerListInputSLZ:
    """测试 MCPServerListInputSLZ 序列化器"""

    def test_validate_categories_single(self):
        """测试单个分类"""
        data = {"categories": "official"}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["categories"] == ["official"]

    def test_validate_categories_multiple(self):
        """测试多个分类（逗号分隔）"""
        data = {"categories": "official,DevOps,featured"}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["categories"] == ["official", "DevOps", "featured"]

    def test_validate_categories_multiple_with_spaces(self):
        """测试多个分类带空格"""
        data = {"categories": " official , DevOps , featured "}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["categories"] == ["official", "DevOps", "featured"]

    def test_validate_categories_empty_string(self):
        """测试空字符串"""
        data = {"categories": ""}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["categories"] == []

    def test_validate_categories_not_provided(self):
        """测试未提供分类参数"""
        data = {}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        # 未提供时，categories 字段不在 validated_data 中或为空列表
        categories = slz.validated_data.get("categories")
        assert categories is None or categories == []

    def test_validate_categories_with_empty_segments(self):
        """测试带空段的分类（如 'official,,DevOps'）"""
        data = {"categories": "official,,DevOps,"}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        # 空段应该被过滤掉
        assert slz.validated_data["categories"] == ["official", "DevOps"]

    def test_validate_categories_only_spaces(self):
        """测试只有空格的分类"""
        data = {"categories": "   "}
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["categories"] == []

    def test_validate_categories_with_other_params(self):
        """测试分类与其他参数一起使用"""
        data = {
            "keyword": "test",
            "categories": "official,DevOps",
            "order_by": "-updated_time",
        }
        slz = MCPServerListInputSLZ(data=data)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["keyword"] == "test"
        assert slz.validated_data["categories"] == ["official", "DevOps"]
        assert slz.validated_data["order_by"] == "-updated_time"
