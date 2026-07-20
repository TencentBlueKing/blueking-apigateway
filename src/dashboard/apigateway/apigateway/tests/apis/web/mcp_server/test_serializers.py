# -*- coding: utf-8 -*-
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
from unittest.mock import patch
from uuid import uuid4

import pytest
from ddf import G

from apigateway.apis.web.constants import ExportTypeEnum
from apigateway.apis.web.mcp_server.serializers import (
    GatewayMCPServerAppPermissionExportInputSLZ,
    GatewayMCPServerAppPermissionListInputSLZ,
    GatewayMCPServerAppPermissionListOutputSLZ,
    MCPServerCategoryOutputSLZ,
    MCPServerCreateInputSLZ,
    MCPServerListInputSLZ,
    MCPServerUpdateInputSLZ,
)
from apigateway.apps.mcp_server.constants import (
    MCPServerAppPermissionApplyStatusEnum,
    MCPServerAppPermissionGrantTypeEnum,
    MCPServerStatusEnum,
)
from apigateway.apps.mcp_server.models import (
    MCPServer,
    MCPServerAppPermission,
    MCPServerAppPermissionApply,
    MCPServerCategory,
)
from apigateway.common.constants import CallSourceTypeEnum, LanguageCodeEnum
from apigateway.core.constants import ResourceKindEnum
from apigateway.core.models import Release

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

    def test_validate_resource_names_rejects_ai_resource(self, fake_gateway, fake_stage, fake_resource_version):
        fake_resource_version.data = [{"name": "ai-resource", "kind": ResourceKindEnum.AI.value}]
        fake_resource_version.save()
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)
        data = {
            "name": "test-mcp-server",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["ai-resource"],
            "tool_names": ["ai-resource"],
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"ai-resource"},
        }

        slz = MCPServerCreateInputSLZ(data=data, context=context)

        assert not slz.is_valid()
        assert "模型代理 API 不能作为 MCP Tool" in str(slz.errors["resource_names"])

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

    def test_validate_resource_names_rejects_ai_resource(self, fake_gateway, fake_stage, fake_resource_version):
        fake_resource_version.data = [{"name": "ai-resource", "kind": ResourceKindEnum.AI.value}]
        fake_resource_version.save()
        G(Release, gateway=fake_gateway, stage=fake_stage, resource_version=fake_resource_version)
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "resource_names": ["ai-resource"],
            "tool_names": ["ai-resource"],
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            context={"valid_resource_names": {"ai-resource"}},
        )

        assert not slz.is_valid()
        assert "模型代理 API 不能作为 MCP Tool" in str(slz.errors["resource_names"])

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


class TestMCPServerCreateInputSLZOAuth2:
    """测试 MCPServerCreateInputSLZ 序列化器的 OAuth2 相关功能"""

    @patch("apigateway.biz.validators.MCPServerHandler.get_valid_resource_names")
    def test_create_with_oauth2_public_client_enabled(self, mock_get_valid, fake_gateway, fake_stage):
        """测试创建时 oauth2_public_client_enabled=True"""
        mock_get_valid.return_value = {"resource1", "resource2"}

        data = {
            "name": "test-mcp-oauth2",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            "oauth2_public_client_enabled": True,
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }

        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["oauth2_public_client_enabled"] is True

    @patch("apigateway.biz.validators.MCPServerHandler.get_valid_resource_names")
    def test_create_with_oauth2_disabled(self, mock_get_valid, fake_gateway, fake_stage):
        """测试创建时 oauth2_public_client_enabled=False"""
        mock_get_valid.return_value = {"resource1", "resource2"}

        data = {
            "name": "test-mcp-no-oauth2",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
            "oauth2_public_client_enabled": False,
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }

        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["oauth2_public_client_enabled"] is False

    @patch("apigateway.biz.validators.MCPServerHandler.get_valid_resource_names")
    def test_create_default_oauth2_disabled(self, mock_get_valid, fake_gateway, fake_stage):
        """测试创建时不传 oauth2_public_client_enabled，默认为 False"""
        mock_get_valid.return_value = {"resource1", "resource2"}

        data = {
            "name": "test-mcp-default",
            "description": "Test description",
            "stage_id": fake_stage.id,
            "is_public": True,
            "resource_names": ["resource1", "resource2"],
            "tool_names": ["resource1", "resource2"],
        }
        context = {
            "gateway": fake_gateway,
            "source": CallSourceTypeEnum.Web,
            "valid_resource_names": {"resource1", "resource2"},
        }

        slz = MCPServerCreateInputSLZ(data=data, context=context)
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["oauth2_public_client_enabled"] is False


class TestMCPServerUpdateInputSLZOAuth2:
    """测试 MCPServerUpdateInputSLZ 序列化器的 OAuth2 相关功能"""

    def test_update_with_oauth2_public_client_enabled(self, fake_gateway, fake_stage):
        """测试更新时设置 oauth2_public_client_enabled=True"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage, status=MCPServerStatusEnum.ACTIVE.value)
        data = {
            "description": "Updated description",
            "oauth2_public_client_enabled": True,
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            partial=True,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["oauth2_public_client_enabled"] is True

    def test_update_with_oauth2_disabled(self, fake_gateway, fake_stage):
        """测试更新时设置 oauth2_public_client_enabled=False"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            oauth2_public_client_enabled=True,
        )
        data = {
            "description": "Updated description",
            "oauth2_public_client_enabled": False,
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            partial=True,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["oauth2_public_client_enabled"] is False

    def test_partial_update_without_oauth2(self, fake_gateway, fake_stage):
        """测试部分更新时不传 oauth2_public_client_enabled，不影响已有值"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            oauth2_public_client_enabled=True,
        )
        data = {
            "description": "Updated description",
        }
        slz = MCPServerUpdateInputSLZ(
            instance=mcp_server,
            data=data,
            partial=True,
            context={"valid_resource_names": {"resource1", "resource2"}},
        )
        assert slz.is_valid(), slz.errors
        assert "oauth2_public_client_enabled" not in slz.validated_data


class TestGatewayMCPServerAppPermissionListInputSLZ:
    """测试网关级 MCPServer 应用权限列表输入序列化器"""

    def test_validate_empty(self):
        slz = GatewayMCPServerAppPermissionListInputSLZ(data={})
        assert slz.is_valid(), slz.errors

    def test_validate_with_mcp_server_id(self):
        slz = GatewayMCPServerAppPermissionListInputSLZ(data={"mcp_server_id": 1})
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["mcp_server_id"] == 1

    def test_validate_with_bk_app_code(self):
        slz = GatewayMCPServerAppPermissionListInputSLZ(data={"bk_app_code": "test-app"})
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["bk_app_code"] == "test-app"

    def test_validate_with_grant_type(self):
        slz = GatewayMCPServerAppPermissionListInputSLZ(
            data={"grant_type": MCPServerAppPermissionGrantTypeEnum.APPLY.value}
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["grant_type"] == MCPServerAppPermissionGrantTypeEnum.APPLY.value

    def test_validate_with_all_params(self):
        slz = GatewayMCPServerAppPermissionListInputSLZ(
            data={
                "mcp_server_id": 1,
                "bk_app_code": "test-app",
                "grant_type": MCPServerAppPermissionGrantTypeEnum.GRANT.value,
            }
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["mcp_server_id"] == 1
        assert slz.validated_data["bk_app_code"] == "test-app"
        assert slz.validated_data["grant_type"] == MCPServerAppPermissionGrantTypeEnum.GRANT.value


class TestGatewayMCPServerAppPermissionListOutputSLZ:
    """测试网关级 MCPServer 应用权限列表输出序列化器"""

    def test_output_grant_type(self, fake_gateway, fake_stage):
        """测试主动授权类型的序列化输出"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp",
            title="测试MCP",
        )
        permission = G(
            MCPServerAppPermission,
            mcp_server=mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
        )
        slz = GatewayMCPServerAppPermissionListOutputSLZ(permission, context={})
        data = slz.data
        assert data["bk_app_code"] == "test-app"
        assert data["grant_type"] == MCPServerAppPermissionGrantTypeEnum.GRANT.value
        assert data["mcp_server"]["name"] == "test-mcp"
        assert data["mcp_server"]["id"] == mcp_server.id

    def test_output_apply_type_with_record(self, fake_gateway, fake_stage):
        """测试申请授权类型（有关联审批记录）的序列化输出"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp",
        )
        permission = G(
            MCPServerAppPermission,
            mcp_server=mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
        )
        apply_record = G(
            MCPServerAppPermissionApply,
            mcp_server=mcp_server,
            bk_app_code="test-app",
            applied_by="test_user",
            handled_by="admin",
            status=MCPServerAppPermissionApplyStatusEnum.APPROVED.value,
            is_deleted=False,
        )
        slz = GatewayMCPServerAppPermissionListOutputSLZ(
            permission,
            context={"apply_record_map": {(mcp_server.id, "test-app"): apply_record}},
        )
        data = slz.data
        assert data["bk_app_code"] == "test-app"
        assert data["grant_type"] == MCPServerAppPermissionGrantTypeEnum.APPLY.value
        # APPLY 类型应该通过审批单获取 handled_by
        assert data["handled_by"] == "admin"

    def test_output_apply_type_without_record(self, fake_gateway, fake_stage):
        """测试申请授权类型（无关联审批记录）的序列化输出，应回退到 permission 字段"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp",
        )
        permission = G(
            MCPServerAppPermission,
            mcp_server=mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.APPLY.value,
            created_by="creator_user",
            updated_by="updater_user",
        )
        slz = GatewayMCPServerAppPermissionListOutputSLZ(permission, context={})
        data = slz.data
        assert data["bk_app_code"] == "test-app"
        assert data["grant_type"] == MCPServerAppPermissionGrantTypeEnum.APPLY.value
        # 无审批记录时，applied_by 回退到 updated_by
        assert data["applied_by"] == "updater_user"

    def test_output_grant_type_with_operator(self, fake_gateway, fake_stage):
        """测试主动授权类型时，handled_by 返回操作人"""
        mcp_server = G(
            MCPServer,
            gateway=fake_gateway,
            stage=fake_stage,
            name="test-mcp",
        )
        permission = G(
            MCPServerAppPermission,
            mcp_server=mcp_server,
            bk_app_code="test-app",
            grant_type=MCPServerAppPermissionGrantTypeEnum.GRANT.value,
            created_by="grant_user",
        )
        slz = GatewayMCPServerAppPermissionListOutputSLZ(permission, context={})
        data = slz.data
        assert data["handled_by"] == "grant_user"


class TestGatewayMCPServerAppPermissionExportInputSLZ:
    """测试网关级 MCPServer 应用权限导出输入序列化器"""

    def test_validate_export_type_all(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(data={"export_type": ExportTypeEnum.ALL.value})
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["export_type"] == ExportTypeEnum.ALL.value

    def test_validate_export_type_filtered(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(data={"export_type": ExportTypeEnum.FILTERED.value})
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["export_type"] == ExportTypeEnum.FILTERED.value

    def test_validate_export_type_selected(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(
            data={"export_type": ExportTypeEnum.SELECTED.value, "selected_ids": [1, 2, 3]}
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["export_type"] == ExportTypeEnum.SELECTED.value
        assert slz.validated_data["selected_ids"] == [1, 2, 3]

    def test_validate_export_type_selected_without_ids(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(data={"export_type": ExportTypeEnum.SELECTED.value})
        assert not slz.is_valid()
        assert "non_field_errors" in slz.errors

    def test_validate_export_type_selected_with_empty_ids(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(
            data={"export_type": ExportTypeEnum.SELECTED.value, "selected_ids": []}
        )
        assert not slz.is_valid()
        assert "non_field_errors" in slz.errors

    def test_validate_export_type_missing(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(data={})
        assert not slz.is_valid()
        assert "export_type" in slz.errors

    def test_validate_with_filter_params(self):
        slz = GatewayMCPServerAppPermissionExportInputSLZ(
            data={
                "export_type": ExportTypeEnum.FILTERED.value,
                "mcp_server_id": 1,
                "bk_app_code": "test",
                "grant_type": MCPServerAppPermissionGrantTypeEnum.GRANT.value,
            }
        )
        assert slz.is_valid(), slz.errors
        assert slz.validated_data["mcp_server_id"] == 1
        assert slz.validated_data["bk_app_code"] == "test"
