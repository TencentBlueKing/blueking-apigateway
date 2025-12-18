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
import logging
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple

from celery import shared_task

from apigateway.biz.mcp_server.prompt import MCPServerPromptHandler

logger = logging.getLogger(__name__)


def _collect_prompt_ids(
    mcp_servers_with_prompts: List[Tuple[int, List[Dict[str, Any]]]],
) -> Dict[int, List[Tuple[int, Dict[str, Any], int]]]:
    """
    收集所有 prompt_ids 及其对应的 mcp_server 信息

    Returns:
        Dict: prompt_id -> [(mcp_server_id, prompt_data, index), ...]
    """
    prompt_id_to_mcp_servers: Dict[int, List[Tuple[int, Dict[str, Any], int]]] = defaultdict(list)

    for mcp_server_id, prompts in mcp_servers_with_prompts:
        for idx, prompt in enumerate(prompts):
            prompt_id = prompt.get("id")
            if prompt_id:
                prompt_id_to_mcp_servers[prompt_id].append((mcp_server_id, prompt, idx))

    return prompt_id_to_mcp_servers


def _find_prompts_need_update(
    prompt_id_to_mcp_servers: Dict[int, List[Tuple[int, Dict[str, Any], int]]],
    remote_updated_times: Dict[int, str],
) -> Set[int]:
    """
    比对更新时间，找出需要更新的 prompt_ids
    """
    need_update_prompt_ids: Set[int] = set()

    for prompt_id, mcp_server_infos in prompt_id_to_mcp_servers.items():
        remote_updated_time = remote_updated_times.get(prompt_id)
        if not remote_updated_time:
            # 远程不存在该 prompt，跳过
            continue

        # 检查本地存储的更新时间是否与远程一致
        for _mcp_server_id, prompt_data, _idx in mcp_server_infos:
            local_updated_time = prompt_data.get("updated_time", "")
            if local_updated_time != remote_updated_time:
                need_update_prompt_ids.add(prompt_id)
                break

    return need_update_prompt_ids


def _build_mcp_server_prompts_to_update(
    mcp_servers_with_prompts: List[Tuple[int, List[Dict[str, Any]]]],
    updated_prompts_map: Dict[int, Dict[str, Any]],
) -> Dict[int, List[Dict[str, Any]]]:
    """
    构建需要更新的 mcp_server prompts 数据
    """
    mcp_server_prompts_to_update: Dict[int, List[Dict[str, Any]]] = {}

    for mcp_server_id, prompts in mcp_servers_with_prompts:
        updated = False
        new_prompts = []

        for prompt in prompts:
            prompt_id = prompt.get("id")
            if prompt_id and prompt_id in updated_prompts_map:
                # 使用远程的最新数据
                new_prompts.append(updated_prompts_map[prompt_id])
                updated = True
            else:
                # 保持原有数据
                new_prompts.append(prompt)

        if updated:
            mcp_server_prompts_to_update[mcp_server_id] = new_prompts

    return mcp_server_prompts_to_update


def _batch_update_mcp_server_prompts(mcp_server_prompts_to_update: Dict[int, List[Dict[str, Any]]]) -> int:
    """
    批量更新 MCPServer 的 prompts 数据

    Returns:
        int: 成功更新的 MCPServer 数量
    """
    update_count = 0
    for mcp_server_id, new_prompts in mcp_server_prompts_to_update.items():
        try:
            MCPServerPromptHandler.update_prompts_content(mcp_server_id, new_prompts)
            update_count += 1
            logger.info("Updated prompts for mcp_server_id=%d", mcp_server_id)
        except Exception:
            logger.exception("Failed to update prompts for mcp_server_id=%d", mcp_server_id)

    return update_count


def _fetch_remote_updated_times(all_prompt_ids: List[int]) -> Optional[Dict[int, str]]:
    """
    从第三方平台获取 prompts 的更新时间
    """
    try:
        return MCPServerPromptHandler.fetch_remote_prompts_updated_time(all_prompt_ids)
    except Exception:
        logger.exception("Failed to fetch remote prompts updated time")
        return None


def _fetch_updated_prompts(need_update_prompt_ids: Set[int]) -> Optional[Dict[int, Dict[str, Any]]]:
    """
    从第三方平台获取需要更新的 prompts 完整数据

    Returns:
        Dict: prompt_id -> prompt_data 的映射，失败返回 None
    """
    try:
        updated_prompts = MCPServerPromptHandler.fetch_remote_prompts_by_ids(list(need_update_prompt_ids))
    except Exception:
        logger.exception("Failed to fetch remote prompts by ids")
        return None

    if not updated_prompts:
        return {}

    return {p["id"]: p for p in updated_prompts if p.get("id")}


@shared_task(name="apigateway.apps.mcp_server.tasks.sync_mcp_server_prompts", ignore_result=True)
def sync_mcp_server_prompts():
    """
    同步所有 MCPServer 绑定的 prompts 数据

    工作流程：
    1. 查出所有配置了 prompts 的 MCPServer
    2. 按 MCPServer 维度遍历，收集所有 prompt_ids
    3. 批量从第三方平台获取 prompts 的更新时间
    4. 比对更新时间，找出需要更新的 prompt_ids
    5. 批量从第三方平台获取需要更新的 prompts 完整数据
    6. 更新本地存储的 prompts 数据
    """
    logger.info("Starting sync_mcp_server_prompts task")

    # 1. 获取所有配置了 prompts 的 MCPServer
    mcp_servers_with_prompts = MCPServerPromptHandler.get_all_mcp_servers_with_prompts()
    if not mcp_servers_with_prompts:
        logger.info("No MCPServer with prompts found, skip sync")
        return

    logger.info("Found %d MCPServers with prompts", len(mcp_servers_with_prompts))

    # 2. 收集所有 prompt_ids
    prompt_id_to_mcp_servers = _collect_prompt_ids(mcp_servers_with_prompts)
    all_prompt_ids = list(prompt_id_to_mcp_servers.keys())
    if not all_prompt_ids:
        logger.info("No prompt_ids found, skip sync")
        return

    logger.info("Found %d unique prompt_ids to check", len(all_prompt_ids))

    # 3. 批量从第三方平台获取 prompts 的更新时间
    remote_updated_times = _fetch_remote_updated_times(all_prompt_ids)
    if not remote_updated_times:
        logger.info("No remote updated times returned, skip sync")
        return

    # 4. 比对更新时间，找出需要更新的 prompt_ids
    need_update_prompt_ids = _find_prompts_need_update(prompt_id_to_mcp_servers, remote_updated_times)
    if not need_update_prompt_ids:
        logger.info("All prompts are up to date, skip sync")
        return

    logger.info("Found %d prompts need to update", len(need_update_prompt_ids))

    # 5. 批量从第三方平台获取需要更新的 prompts 完整数据
    updated_prompts_map = _fetch_updated_prompts(need_update_prompt_ids)
    if not updated_prompts_map:
        logger.info("No updated prompts data returned, skip sync")
        return

    # 6. 更新本地存储的 prompts 数据
    mcp_server_prompts_to_update = _build_mcp_server_prompts_to_update(mcp_servers_with_prompts, updated_prompts_map)
    update_count = _batch_update_mcp_server_prompts(mcp_server_prompts_to_update)

    logger.info("sync_mcp_server_prompts task completed, updated %d MCPServers", update_count)
