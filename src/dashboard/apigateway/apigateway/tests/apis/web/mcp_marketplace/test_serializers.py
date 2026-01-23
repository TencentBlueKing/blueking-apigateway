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

from apigateway.apis.web.mcp_marketplace.serializers import MCPServerCategoryOutputSLZ
from apigateway.apps.mcp_server.models import MCPServerCategory
from apigateway.common.constants import LanguageCodeEnum

pytestmark = pytest.mark.django_db


class TestMCPServerCategoryOutputSLZ:
    """测试 MCPServerCategoryOutputSLZ 序列化器的国际化功能"""

    @patch("apigateway.apis.web.mcp_marketplace.serializers.get_current_language_code")
    def test_display_name_returns_name_for_english(self, mock_get_language):
        """测试英文环境返回 name"""
        mock_get_language.return_value = LanguageCodeEnum.EN.value
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category, context={"category_stats": {}})
        assert slz.data["display_name"] == category.name
        assert slz.data["name"] == category.name

    @patch("apigateway.apis.web.mcp_marketplace.serializers.get_current_language_code")
    def test_display_name_returns_display_name_for_chinese(self, mock_get_language):
        """测试中文环境返回 display_name"""
        mock_get_language.return_value = LanguageCodeEnum.ZH_HANS.value
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category, context={"category_stats": {}})
        assert slz.data["display_name"] == "开发运维"
        assert slz.data["name"] == category.name

    @patch("apigateway.apis.web.mcp_marketplace.serializers.get_current_language_code")
    def test_display_name_returns_display_name_for_other_languages(self, mock_get_language):
        """测试其他语言环境返回 display_name"""
        mock_get_language.return_value = "zh-hant"  # 繁体中文
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category, context={"category_stats": {}})
        assert slz.data["display_name"] == "开发运维"

    @patch("apigateway.apis.web.mcp_marketplace.serializers.get_current_language_code")
    def test_mcp_server_count(self, mock_get_language):
        """测试 mcp_server_count 字段"""
        mock_get_language.return_value = LanguageCodeEnum.ZH_HANS.value
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category, context={"category_stats": {category.id: 5}})
        assert slz.data["mcp_server_count"] == 5

    @patch("apigateway.apis.web.mcp_marketplace.serializers.get_current_language_code")
    def test_mcp_server_count_default_zero(self, mock_get_language):
        """测试 mcp_server_count 默认返回 0"""
        mock_get_language.return_value = LanguageCodeEnum.ZH_HANS.value
        category = G(MCPServerCategory, name=f"DevOps-{uuid4().hex[:8]}", display_name="开发运维")

        slz = MCPServerCategoryOutputSLZ(category, context={"category_stats": {}})
        assert slz.data["mcp_server_count"] == 0
