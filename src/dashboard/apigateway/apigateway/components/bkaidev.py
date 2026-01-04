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
from typing import Any, Dict, List, Optional

from django.conf import settings

from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.user_credentials import UserCredentials
from apigateway.utils.url import url_join

from .http import http_get, http_post
from .utils import do_blueking_http_request, gen_gateway_headers

logger = logging.getLogger(__name__)

# Mock 数据（模拟第三方 API 返回格式）
_MOCK_PROMPTS: List[Dict[str, Any]] = [
    {
        "prompt_id": 1,
        "prompt_code": "prompt_001",
        "prompt_name": "代码审查助手",
        "prompt_content": "你是一个专业的代码审查专家，请帮我审查以下代码，指出潜在的问题、安全隐患和优化建议。\n\n代码：\n{{code}}",
        "updated_at": "2025-12-15T10:00:00Z",
        "updated_by": "admin",
        "tag_names": ["代码", "审查", "开发工具"],
        "generate_type": "public",
        "is_public": True,
        "space_id": "devops",
        "space_name": "DevOps",
    },
    {
        "prompt_id": 2,
        "prompt_code": "prompt_002",
        "prompt_name": "API 文档生成器",
        "prompt_content": "请根据以下 {{language}} 代码生成详细的 API 文档，包括接口描述、参数说明、返回值说明和使用示例。\n\n代码：\n{{code}}",
        "updated_at": "2025-12-14T15:30:00Z",
        "updated_by": "developer",
        "tag_names": ["文档", "API", "自动化"],
        "generate_type": "public",
        "is_public": True,
        "space_id": "devops",
        "space_name": "DevOps",
    },
    {
        "prompt_id": 3,
        "prompt_code": "prompt_003",
        "prompt_name": "SQL 优化顾问",
        "prompt_content": "你是一个数据库优化专家，请分析以下 SQL 语句，提供性能优化建议和最佳实践。\n\n数据库类型：{{db_type}}\nSQL 语句：\n{{sql}}",
        "updated_at": "2025-12-13T09:15:00Z",
        "updated_by": "dba_user",
        "tag_names": ["数据库", "SQL", "性能优化"],
        "generate_type": "space",
        "is_public": False,
        "space_id": "dba",
        "space_name": "DBA",
    },
    {
        "prompt_id": 4,
        "prompt_code": "prompt_004",
        "prompt_name": "单元测试生成器",
        "prompt_content": "请为以下 {{language}} 函数生成完整的单元测试用例，包括正常情况、边界情况和异常情况的测试。\n\n函数代码：\n{{function_code}}",
        "updated_at": "2025-12-12T14:20:00Z",
        "updated_by": "qa_engineer",
        "tag_names": ["测试", "单元测试", "质量保证"],
        "generate_type": "public",
        "is_public": True,
        "space_id": "qa",
        "space_name": "QA",
    },
    {
        "prompt_id": 5,
        "prompt_code": "prompt_005",
        "prompt_name": "错误日志分析",
        "prompt_content": "请分析以下错误日志，找出问题根因并提供解决方案。\n\n应用名称：{{app_name}}\n错误日志：\n{{error_log}}",
        "updated_at": "2025-12-11T11:45:00Z",
        "updated_by": "ops_admin",
        "tag_names": ["运维", "日志分析", "故障排查"],
        "generate_type": "space",
        "is_public": False,
        "space_id": "ops",
        "space_name": "OPS",
    },
]


def _convert_prompt(remote_prompt: Dict[str, Any]) -> Dict[str, Any]:
    """
    将第三方 API 返回的 prompt 数据转换为内部格式

    字段映射：
        - prompt_id -> id
        - prompt_name -> name
        - prompt_code -> code
        - prompt_content -> content
        - updated_at -> updated_time
        - updated_by -> updated_by
        - tag_names -> labels
        - is_public -> is_public
        - space_id -> space_code
        - space_name -> space_name
    """
    return {
        "id": remote_prompt.get("prompt_id", 0),
        "name": remote_prompt.get("prompt_name", ""),
        "code": remote_prompt.get("prompt_code", ""),
        "content": remote_prompt.get("prompt_content", ""),
        "updated_time": remote_prompt.get("updated_at", ""),
        "updated_by": remote_prompt.get("updated_by", ""),
        "labels": remote_prompt.get("tag_names", []),
        "is_public": remote_prompt.get("is_public", False),
        "space_code": remote_prompt.get("space_id", ""),
        "space_name": remote_prompt.get("space_name", ""),
    }


def _convert_prompts(remote_prompts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """批量转换 prompts 数据"""
    return [_convert_prompt(p) for p in remote_prompts]


def _get_mock_prompts_by_keyword() -> List[Dict[str, Any]]:
    """返回mock prompts（返回原始格式，不做转换）

    模拟真实 API 行为：列表接口不返回 prompt_content 字段
    """
    # 列表接口不返回 content，移除 prompt_content 字段
    return [{k: v for k, v in p.items() if k != "prompt_content"} for p in _MOCK_PROMPTS]


def _get_mock_prompts_by_ids(prompt_ids: List[int]) -> List[Dict[str, Any]]:
    """根据 ID 列表获取 mock prompts（返回原始格式，不做转换）"""
    id_set = set(prompt_ids)
    return [p for p in _MOCK_PROMPTS if p["prompt_id"] in id_set]


def _get_mock_prompts_updated_time(prompt_ids: List[int]) -> Dict[int, str]:
    """获取 mock prompts 的更新时间"""
    id_set = set(prompt_ids)
    return {p["prompt_id"]: p["updated_at"] for p in _MOCK_PROMPTS if p["prompt_id"] in id_set}


def _call_bkaidev_api(
    http_func,
    path: str,
    data: Optional[Dict[str, Any]] = None,
    user_credentials: Optional[UserCredentials] = None,
    more_headers: Optional[Dict[str, str]] = None,
    timeout: int = 30,
) -> Any:
    """
    统一调用 BKAIDev 平台 API

    Args:
        http_func: HTTP 请求函数（http_get 或 http_post）
        path: API 路径
        data: 请求数据
        more_headers: 额外的请求头
        timeout: 超时时间

    Returns:
        响应数据，do_blueking_http_request 返回 resp_data["data"]
        不同接口返回格式不同：
        - /openapi/aidev/user_mode/resource/prompt/manage/ 返回 list
        - /openapi/aidev/resource/v1/prompts/batch/ 返回 dict {"results": [...]}

    Raises:
        error_codes.REMOTE_REQUEST_ERROR: 请求失败时抛出
    """
    headers = gen_gateway_headers(user_credentials=user_credentials)
    if more_headers:
        headers.update(more_headers)

    url = url_join(settings.BKAIDEV_URL_PREFIX, path)

    return do_blueking_http_request("bkaidev", http_func, url, data, headers, timeout)


def fetch_prompts_list(user_credentials: UserCredentials) -> List[Dict[str, Any]]:
    """
    从 BKAIDev 平台获取 prompts 列表

    调用接口: list_user_mode_resource_prompt_manage (GET)
    路径: /openapi/aidev/user_mode/resource/prompt/manage/

    Args:
        user_credentials: 用户认证相关信息

    Returns:
        prompts 列表（已转换为内部格式）
    """
    # Mock 模式：返回 mock 数据
    if settings.BKAIDEV_USE_MOCK:
        logger.info("BKAIDEV_USE_MOCK is enabled, returning mock data for fetch_prompts_list")
        return _convert_prompts(_get_mock_prompts_by_keyword())

    if not settings.BKAIDEV_URL_PREFIX:
        raise error_codes.REMOTE_REQUEST_ERROR.format("BKAIDEV_URL_PREFIX is not configured")
    result = _call_bkaidev_api(
        http_get,
        "/openapi/aidev/user_mode/resource/prompt/manage/",
        user_credentials=user_credentials,
        timeout=settings.BKAIDEV_API_TIMEOUT,
    )
    # 该接口返回 data 直接是 list
    if not isinstance(result, list):
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"fetch_prompts_list expected list response, got {type(result).__name__}"
        )
    return _convert_prompts(result)


def fetch_prompts_by_ids(prompt_ids: List[int], with_content: bool = True) -> List[Dict[str, Any]]:
    """
    根据 prompt IDs 从 BKAIDev 平台批量获取 prompts 详情

    调用接口: create_platform_resource_v1_prompts_batch (POST)
    路径: /openapi/aidev/resource/v1/prompts/batch/

    Args:
        prompt_ids: prompt ID 列表 (整数类型)
        with_content: 是否返回 prompt 内容，默认 True

    Returns:
        prompts 详情列表（已转换为内部格式）
    """
    if not prompt_ids:
        return []

    # Mock 模式：返回 mock 数据
    if settings.BKAIDEV_USE_MOCK:
        logger.info("BKAIDEV_USE_MOCK is enabled, returning mock data for fetch_prompts_by_ids")
        return _convert_prompts(_get_mock_prompts_by_ids(prompt_ids))

    if not settings.BKAIDEV_URL_PREFIX:
        raise error_codes.REMOTE_REQUEST_ERROR.format("BKAIDEV_URL_PREFIX is not configured")

    data = {"ids": prompt_ids, "type": "prompt", "with_content": with_content}

    result = _call_bkaidev_api(
        http_post, "/openapi/aidev/resource/v1/prompts/batch/", data, timeout=settings.BKAIDEV_API_TIMEOUT
    )
    # 该接口返回 data 是 dict，包含 results 字段
    if isinstance(result, dict):
        result = result.get("results", [])
    if not isinstance(result, list):
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"fetch_prompts_by_ids expected list response, got {type(result).__name__}"
        )
    return _convert_prompts(result)


def fetch_prompts_updated_time(prompt_ids: List[int]) -> Dict[int, str]:
    """
    从 BKAIDev 平台批量获取 prompts 的更新时间

    调用接口: create_platform_resource_v1_prompts_batch (POST)
    路径: /openapi/aidev/resource/v1/prompts/batch/
    参数: with_content=False 只返回更新时间

    Args:
        prompt_ids: prompt ID 列表 (整数类型)

    Returns:
        prompt_id -> updated_time 的映射
        例如: {1: "2025-12-12T10:00:00Z", 2: "2025-12-11T15:30:00Z"}
    """
    if not prompt_ids:
        return {}

    # Mock 模式：返回 mock 数据
    if settings.BKAIDEV_USE_MOCK:
        logger.info("BKAIDEV_USE_MOCK is enabled, returning mock data for fetch_prompts_updated_time")
        return _get_mock_prompts_updated_time(prompt_ids)

    if not settings.BKAIDEV_URL_PREFIX:
        raise error_codes.REMOTE_REQUEST_ERROR.format("BKAIDEV_URL_PREFIX is not configured")

    # 使用 with_content=False 只获取更新时间
    data = {"ids": prompt_ids, "type": "prompt", "with_content": False}

    result = _call_bkaidev_api(
        http_post, "/openapi/aidev/resource/v1/prompts/batch/", data, timeout=settings.BKAIDEV_API_TIMEOUT
    )
    # 该接口返回 data 是 dict，包含 results 字段
    if isinstance(result, dict):
        result = result.get("results", [])
    if not isinstance(result, list):
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"fetch_prompts_updated_time expected list response, got {type(result).__name__}"
        )
    return {item.get("prompt_id"): item.get("updated_at", "") for item in result if item.get("prompt_id")}
