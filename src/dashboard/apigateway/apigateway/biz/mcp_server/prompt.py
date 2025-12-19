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
import logging
from typing import Any, Dict, List, Tuple

from apigateway.apps.mcp_server.constants import MCPServerExtendTypeEnum
from apigateway.apps.mcp_server.models import MCPServerExtend
from apigateway.components import bkaidev

logger = logging.getLogger(__name__)


class MCPServerPromptHandler:
    """MCPServer Prompt 相关处理器（供异步任务调用）"""

    @staticmethod
    def fetch_remote_prompts_by_ids(prompt_ids: List[int]) -> List[Dict[str, Any]]:
        """根据 prompt IDs 从 BKAIDev 平台批量获取 prompts 详情

        Args:
            prompt_ids: prompt ID 列表 (整数类型)

        Returns:
            prompts 详情列表
        """
        return bkaidev.fetch_prompts_by_ids(prompt_ids=prompt_ids)

    @staticmethod
    def fetch_remote_prompts_updated_time(prompt_ids: List[int]) -> Dict[int, str]:
        """从 BKAIDev 平台批量获取 prompts 的更新时间

        Args:
            prompt_ids: prompt ID 列表 (整数类型)

        Returns:
            prompt_id -> updated_time 的映射
        """
        return bkaidev.fetch_prompts_updated_time(prompt_ids=prompt_ids)

    @staticmethod
    def get_all_mcp_servers_with_prompts() -> List[Tuple[int, List[Dict[str, Any]]]]:
        """获取所有配置了 prompts 的 MCPServer

        Returns:
            [(mcp_server_id, prompts_list), ...]
        """
        extends = MCPServerExtend.objects.filter(
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).exclude(content="")

        result = []
        for extend in extends:
            try:
                prompts = json.loads(extend.content)
                if prompts:
                    result.append((extend.mcp_server_id, prompts))
            except json.JSONDecodeError:
                logger.exception("Failed to parse prompts content for mcp_server_id=%s", extend.mcp_server_id)
                continue

        return result

    @staticmethod
    def update_prompts_content(mcp_server_id: int, prompts: List[Dict[str, Any]]) -> None:
        """更新 MCPServer 的 prompts 内容（用于异步任务同步）

        Args:
            mcp_server_id: MCPServer ID
            prompts: 更新后的 prompts 列表
        """
        content = json.dumps(prompts, ensure_ascii=False)

        MCPServerExtend.objects.filter(
            mcp_server_id=mcp_server_id,
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).update(content=content)
