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
from unittest.mock import patch

import pytest
from ddf import G

from apigateway.apps.mcp_server.constants import MCPServerExtendTypeEnum
from apigateway.apps.mcp_server.models import MCPServer, MCPServerExtend
from apigateway.biz.mcp_server.prompt import MCPServerPromptHandler


class TestMCPServerPromptHandler:
    """测试 MCPServerPromptHandler（供异步任务调用的方法）"""

    @pytest.fixture
    def fake_mcp_server(self, fake_gateway, fake_stage):
        return G(MCPServer, gateway=fake_gateway, stage=fake_stage)

    @pytest.fixture
    def sample_prompts(self):
        return [
            {
                "id": "prompt_001",
                "name": "代码审查助手",
                "description": "帮助进行代码审查",
                "content": "你是一个代码审查专家...",
                "updated_time": "2025-12-15T10:00:00Z",
                "labels": ["代码", "审查"],
                "is_public": True,
                "space_code": "devops",
                "granted_space_codes": ["monitor", "cmdb"],
            },
            {
                "id": "prompt_002",
                "name": "API 文档生成器",
                "description": "根据代码自动生成 API 文档",
                "content": "请根据以下代码生成 API 文档...",
                "updated_time": "2025-12-14T15:30:00Z",
                "labels": ["文档"],
                "is_public": False,
                "space_code": "devops",
                "granted_space_codes": [],
            },
        ]

    # ========== fetch_remote_prompts_by_ids 测试 ==========

    def test_fetch_remote_prompts_by_ids(self):
        mock_prompts = [
            {"id": "prompt_001", "name": "Prompt 1"},
            {"id": "prompt_002", "name": "Prompt 2"},
        ]

        with patch("apigateway.components.bkaidev.fetch_prompts_by_ids", return_value=mock_prompts) as mock_fetch:
            result = MCPServerPromptHandler.fetch_remote_prompts_by_ids(prompt_ids=["prompt_001", "prompt_002"])

            mock_fetch.assert_called_once_with(prompt_ids=["prompt_001", "prompt_002"])
            assert result == mock_prompts

    def test_fetch_remote_prompts_by_ids_empty(self):
        with patch("apigateway.components.bkaidev.fetch_prompts_by_ids", return_value=[]) as mock_fetch:
            result = MCPServerPromptHandler.fetch_remote_prompts_by_ids(prompt_ids=["prompt_001"])

            mock_fetch.assert_called_once_with(prompt_ids=["prompt_001"])
            assert result == []

    # ========== fetch_remote_prompts_updated_time 测试 ==========

    def test_fetch_remote_prompts_updated_time(self):
        mock_result = {
            "prompt_001": "2025-12-15T10:00:00Z",
            "prompt_002": "2025-12-14T15:30:00Z",
        }

        with patch("apigateway.components.bkaidev.fetch_prompts_updated_time", return_value=mock_result) as mock_fetch:
            result = MCPServerPromptHandler.fetch_remote_prompts_updated_time(prompt_ids=["prompt_001", "prompt_002"])

            mock_fetch.assert_called_once_with(prompt_ids=["prompt_001", "prompt_002"])
            assert result == mock_result

    # ========== get_all_mcp_servers_with_prompts 测试 ==========

    def test_get_all_mcp_servers_with_prompts_empty(self):
        """测试没有配置 prompts 的情况"""
        result = MCPServerPromptHandler.get_all_mcp_servers_with_prompts()
        assert result == []

    def test_get_all_mcp_servers_with_prompts(self, fake_gateway, fake_stage, sample_prompts):
        """测试获取所有配置了 prompts 的 MCPServer"""
        mcp_server1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server3 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        # mcp_server1 有 prompts
        G(
            MCPServerExtend,
            mcp_server=mcp_server1,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(sample_prompts),
        )

        # mcp_server2 有 prompts（只有一个）
        G(
            MCPServerExtend,
            mcp_server=mcp_server2,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([sample_prompts[0]]),
        )

        # mcp_server3 没有 prompts（空内容）
        G(
            MCPServerExtend,
            mcp_server=mcp_server3,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content="",
        )

        result = MCPServerPromptHandler.get_all_mcp_servers_with_prompts()

        assert len(result) == 2

        mcp_server_ids = [item[0] for item in result]
        assert mcp_server1.id in mcp_server_ids
        assert mcp_server2.id in mcp_server_ids
        assert mcp_server3.id not in mcp_server_ids

    def test_get_all_mcp_servers_with_prompts_invalid_json(self, fake_gateway, fake_stage, sample_prompts):
        """测试包含无效 JSON 的情况"""
        mcp_server1 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)
        mcp_server2 = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        # mcp_server1 有有效 prompts
        G(
            MCPServerExtend,
            mcp_server=mcp_server1,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps(sample_prompts),
        )

        # mcp_server2 有无效 JSON
        G(
            MCPServerExtend,
            mcp_server=mcp_server2,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content="invalid json",
        )

        result = MCPServerPromptHandler.get_all_mcp_servers_with_prompts()

        # 只返回有效的
        assert len(result) == 1
        assert result[0][0] == mcp_server1.id

    def test_get_all_mcp_servers_with_prompts_empty_list(self, fake_gateway, fake_stage):
        """测试 prompts 为空列表的情况"""
        mcp_server = G(MCPServer, gateway=fake_gateway, stage=fake_stage)

        G(
            MCPServerExtend,
            mcp_server=mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([]),  # 空列表
        )

        result = MCPServerPromptHandler.get_all_mcp_servers_with_prompts()

        # 空列表不应返回
        assert len(result) == 0

    # ========== update_prompts_content 测试 ==========

    def test_update_prompts_content(self, fake_mcp_server, sample_prompts):
        """测试更新 prompts 内容"""
        G(
            MCPServerExtend,
            mcp_server=fake_mcp_server,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
            content=json.dumps([{"id": "old_prompt"}]),
        )

        MCPServerPromptHandler.update_prompts_content(
            mcp_server_id=fake_mcp_server.id,
            prompts=sample_prompts,
        )

        extend = MCPServerExtend.objects.get(
            mcp_server_id=fake_mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        )

        updated_prompts = json.loads(extend.content)
        assert len(updated_prompts) == 2
        assert updated_prompts[0]["id"] == "prompt_001"

    def test_update_prompts_content_not_exists(self, fake_mcp_server, sample_prompts):
        """测试更新不存在的 prompts（不应创建新记录）"""
        MCPServerPromptHandler.update_prompts_content(
            mcp_server_id=fake_mcp_server.id,
            prompts=sample_prompts,
        )

        # 不应创建新记录
        assert not MCPServerExtend.objects.filter(
            mcp_server_id=fake_mcp_server.id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).exists()
