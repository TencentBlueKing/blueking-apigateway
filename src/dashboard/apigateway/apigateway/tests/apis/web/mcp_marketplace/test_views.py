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
import json

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerExtendTypeEnum, MCPServerStatusEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerExtend
from apigateway.core.constants import GatewayStatusEnum, StageStatusEnum

pytestmark = pytest.mark.django_db


@pytest.fixture
def fake_public_mcp_server(fake_gateway, fake_stage, faker):
    """创建一个公开的 MCPServer"""
    # 确保 gateway 和 stage 是激活状态
    fake_gateway.status = GatewayStatusEnum.ACTIVE.value
    fake_gateway.save()
    fake_stage.status = StageStatusEnum.ACTIVE.value
    fake_stage.save()

    return G(
        MCPServer,
        name=faker.pystr()[:20],
        gateway=fake_gateway,
        stage=fake_stage,
        status=MCPServerStatusEnum.ACTIVE.value,
        description=faker.pystr(),
        is_public=True,
        _resource_names="resource1;resource2",
    )


class TestMCPMarketplaceServerListApi:
    def test_list(self, request_view, fake_public_mcp_server):
        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.list",
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "count" in result["data"]

        # 验证返回的数据中包含 updated_time 字段
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_public_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert "updated_time" in mcp_server_data

    def test_list_with_prompts_count(self, request_view, fake_public_mcp_server):
        """测试列表接口返回 prompts_count"""
        # 给 mcp_server 添加 prompts
        G(
            MCPServerExtend,
            mcp_server=fake_public_mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(
                [{"id": 1, "name": "prompt1"}, {"id": 2, "name": "prompt2"}, {"id": 3, "name": "prompt3"}]
            ),
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.list",
        )
        result = resp.json()

        assert resp.status_code == 200

        # 找到对应的数据
        mcp_server_data = next(
            (item for item in result["data"]["results"] if item["id"] == fake_public_mcp_server.id),
            None,
        )
        assert mcp_server_data is not None
        assert mcp_server_data["prompts_count"] == 3

    def test_list_with_keyword(self, request_view, fake_public_mcp_server):
        """测试带关键词过滤"""
        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.list",
            data={"keyword": fake_public_mcp_server.name[:5]},
        )
        result = resp.json()

        assert resp.status_code == 200


class TestMCPMarketplaceServerRetrieveApi:
    def test_retrieve(self, mocker, request_view, fake_public_mcp_server):
        mocker.patch(
            "apigateway.apis.web.mcp_marketplace.views.render_to_string",
            return_value="# Guideline Content",
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], {}),
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.retrieve",
            path_params={"mcp_server_id": fake_public_mcp_server.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["id"] == fake_public_mcp_server.id
        assert result["data"]["name"] == fake_public_mcp_server.name
        assert "updated_time" in result["data"]

    def test_retrieve_with_prompts(self, mocker, request_view, fake_public_mcp_server):
        """测试详情接口返回 prompts 列表（私有 prompt 的 content 为空）"""
        mocker.patch(
            "apigateway.apis.web.mcp_marketplace.views.render_to_string",
            return_value="# Guideline Content",
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], {}),
        )

        # 给 mcp_server 添加 prompts，与 MCPServerPromptItemSLZ 字段一致
        # 包含 1 个公开的和 1 个私有的
        prompts_data = [
            {
                "id": 1001,
                "name": "代码审查助手",
                "code": "code_review",
                "content": "帮助审查代码",
                "updated_time": "2025-12-18 10:00:00",
                "updated_by": "admin",
                "labels": ["code", "review"],
                "is_public": True,
                "space_code": "default",
                "space_name": "默认空间",
            },
            {
                "id": 1002,
                "name": "API 文档生成器",
                "code": "api_doc_gen",
                "content": "生成 API 文档",  # 私有的，content 应该返回空
                "updated_time": "2025-12-18 11:00:00",
                "updated_by": "user1",
                "labels": ["api", "doc"],
                "is_public": False,
                "space_code": "team",
                "space_name": "团队空间",
            },
        ]
        G(
            MCPServerExtend,
            mcp_server=fake_public_mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(prompts_data),
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.retrieve",
            path_params={"mcp_server_id": fake_public_mcp_server.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert result["data"]["prompts_count"] == 2
        assert "prompts" in result["data"]
        # 返回所有 2 个 prompts
        assert len(result["data"]["prompts"]) == 2

        # 第一个是公开的，content 有值
        assert result["data"]["prompts"][0]["id"] == 1001
        assert result["data"]["prompts"][0]["name"] == "代码审查助手"
        assert result["data"]["prompts"][0]["content"] == "帮助审查代码"
        assert result["data"]["prompts"][0]["is_public"] is True

        # 第二个是私有的，content 为空
        assert result["data"]["prompts"][1]["id"] == 1002
        assert result["data"]["prompts"][1]["name"] == "API 文档生成器"
        assert result["data"]["prompts"][1]["content"] == ""  # 私有的 content 为空
        assert result["data"]["prompts"][1]["is_public"] is False
        assert result["data"]["prompts"][1]["space_name"] == "团队空间"

    def test_retrieve_not_public(self, request_view, fake_gateway, fake_stage, faker):
        """测试访问非公开的 MCPServer"""
        mcp_server = G(
            MCPServer,
            name=faker.pystr()[:20],
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.ACTIVE.value,
            is_public=False,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
        )

        assert resp.status_code == 404

    def test_retrieve_inactive(self, request_view, fake_gateway, fake_stage, faker):
        """测试访问未启用的 MCPServer"""
        fake_gateway.status = GatewayStatusEnum.ACTIVE.value
        fake_gateway.save()
        fake_stage.status = StageStatusEnum.ACTIVE.value
        fake_stage.save()

        mcp_server = G(
            MCPServer,
            name=faker.pystr()[:20],
            gateway=fake_gateway,
            stage=fake_stage,
            status=MCPServerStatusEnum.INACTIVE.value,
            is_public=True,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.retrieve",
            path_params={"mcp_server_id": mcp_server.id},
        )

        assert resp.status_code == 404

    def test_retrieve_with_user_custom_doc(self, mocker, request_view, fake_public_mcp_server):
        """测试详情接口返回用户自定义文档"""
        mocker.patch(
            "apigateway.apis.web.mcp_marketplace.views.render_to_string",
            return_value="# Guideline Content",
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], {}),
        )

        # 给 mcp_server 添加用户自定义文档
        custom_doc_content = "# 用户自定义文档\n\n这是一份自定义的使用说明。"
        G(
            MCPServerExtend,
            mcp_server=fake_public_mcp_server,
            type=MCPServerExtendTypeEnum.USER_CUSTOM_DOC.value,
            content=custom_doc_content,
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.retrieve",
            path_params={"mcp_server_id": fake_public_mcp_server.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "user_custom_doc" in result["data"]
        assert result["data"]["user_custom_doc"] == custom_doc_content

    def test_retrieve_without_user_custom_doc(self, mocker, request_view, fake_public_mcp_server):
        """测试详情接口在没有用户自定义文档时返回空字符串"""
        mocker.patch(
            "apigateway.apis.web.mcp_marketplace.views.render_to_string",
            return_value="# Guideline Content",
        )
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tools_resources_and_labels",
            return_value=([], {}),
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.retrieve",
            path_params={"mcp_server_id": fake_public_mcp_server.id},
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "user_custom_doc" in result["data"]
        assert result["data"]["user_custom_doc"] == ""


class TestMCPMarketplaceServerToolDocRetrieveApi:
    def test_retrieve(self, mocker, request_view, fake_public_mcp_server):
        mocker.patch(
            "apigateway.biz.mcp_server.MCPServerHandler.get_tool_doc",
            return_value={
                "type": "markdown",
                "content": "# Tool Doc",
                "updated_time": "2025-12-18T10:00:00Z",
                "schema": {},
            },
        )

        resp = request_view(
            method="GET",
            view_name="mcp_marketplace.server.tool_doc_retrieve",
            path_params={
                "mcp_server_id": fake_public_mcp_server.id,
                "tool_name": "resource1",
            },
        )
        result = resp.json()

        assert resp.status_code == 200
        assert "content" in result["data"]
