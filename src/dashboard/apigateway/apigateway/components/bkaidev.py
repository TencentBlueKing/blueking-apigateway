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
from typing import Any, Dict, List
from urllib.parse import urlparse

from django.conf import settings

from apigateway.common.error_codes import error_codes
from apigateway.utils.local import local
from apigateway.utils.url import url_join

from .http import http_get, http_post
from .utils import gen_gateway_headers

logger = logging.getLogger(__name__)

# Mock 数据
_MOCK_PROMPTS: List[Dict[str, Any]] = [
    {
        "id": "prompt_001",
        "name": "代码审查助手",
        "description": "帮助进行代码审查，发现潜在问题和优化建议",
        "content": "你是一个专业的代码审查专家，请帮我审查以下代码，指出潜在的问题、安全隐患和优化建议。\n\n代码：\n{{code}}",
        "updated_time": "2025-12-15T10:00:00Z",
        "labels": ["代码", "审查", "开发工具"],
        "is_public": True,
        "variables": [
            {"field_name": "code", "field_value": ""},
        ],
    },
    {
        "id": "prompt_002",
        "name": "API 文档生成器",
        "description": "根据代码自动生成 API 文档",
        "content": "请根据以下 {{language}} 代码生成详细的 API 文档，包括接口描述、参数说明、返回值说明和使用示例。\n\n代码：\n{{code}}",
        "updated_time": "2025-12-14T15:30:00Z",
        "labels": ["文档", "API", "自动化"],
        "is_public": True,
        "variables": [
            {"field_name": "language", "field_value": "Python"},
            {"field_name": "code", "field_value": ""},
        ],
    },
    {
        "id": "prompt_003",
        "name": "SQL 优化顾问",
        "description": "分析 SQL 语句并提供优化建议",
        "content": "你是一个数据库优化专家，请分析以下 SQL 语句，提供性能优化建议和最佳实践。\n\n数据库类型：{{db_type}}\nSQL 语句：\n{{sql}}",
        "updated_time": "2025-12-13T09:15:00Z",
        "labels": ["数据库", "SQL", "性能优化"],
        "is_public": False,
        "variables": [
            {"field_name": "db_type", "field_value": "MySQL"},
            {"field_name": "sql", "field_value": ""},
        ],
    },
    {
        "id": "prompt_004",
        "name": "单元测试生成器",
        "description": "为给定的函数生成单元测试用例",
        "content": "请为以下 {{language}} 函数生成完整的单元测试用例，包括正常情况、边界情况和异常情况的测试。\n\n函数代码：\n{{function_code}}",
        "updated_time": "2025-12-12T14:20:00Z",
        "labels": ["测试", "单元测试", "质量保证"],
        "is_public": True,
        "variables": [
            {"field_name": "language", "field_value": "Python"},
            {"field_name": "function_code", "field_value": ""},
        ],
    },
    {
        "id": "prompt_005",
        "name": "错误日志分析",
        "description": "分析错误日志并给出解决方案",
        "content": "请分析以下错误日志，找出问题根因并提供解决方案。\n\n应用名称：{{app_name}}\n错误日志：\n{{error_log}}",
        "updated_time": "2025-12-11T11:45:00Z",
        "labels": ["运维", "日志分析", "故障排查"],
        "is_public": False,
        "variables": [
            {"field_name": "app_name", "field_value": ""},
            {"field_name": "error_log", "field_value": ""},
        ],
    },
]


def _get_mock_prompts_by_keyword(keyword: str = "") -> List[Dict[str, Any]]:
    """根据关键字过滤 mock prompts"""
    if not keyword:
        return _MOCK_PROMPTS

    keyword_lower = keyword.lower()
    return [
        p
        for p in _MOCK_PROMPTS
        if keyword_lower in p["name"].lower()
        or keyword_lower in p["description"].lower()
        or any(keyword_lower in label.lower() for label in p.get("labels", []))
    ]


def _get_mock_prompts_by_ids(prompt_ids: List[str]) -> List[Dict[str, Any]]:
    """根据 ID 列表获取 mock prompts"""
    id_set = set(prompt_ids)
    return [p for p in _MOCK_PROMPTS if p["id"] in id_set]


def _get_mock_prompts_updated_time(prompt_ids: List[str]) -> Dict[str, str]:
    """获取 mock prompts 的更新时间"""
    id_set = set(prompt_ids)
    return {p["id"]: p["updated_time"] for p in _MOCK_PROMPTS if p["id"] in id_set}


def _get_bkaidev_url_prefix() -> str:
    """
    获取 BKAIDev 平台的 URL 前缀

    需要在 settings 中配置 BKAIDEV_URL_PREFIX
    """
    return settings.BKAIDEV_URL_PREFIX


def fetch_prompts_list(username: str, keyword: str = "") -> List[Dict[str, Any]]:
    """
    从 BKAIDev 平台获取 prompts 列表

    Args:
        username: 用户名，用于平台鉴权
        keyword: 搜索关键字

    Returns:
        prompts 列表，格式如下：
        [
            {
                "id": "prompt_001",
                "name": "代码审查助手",
                "description": "帮助进行代码审查的 prompt",
                "content": "你是一个代码审查专家...",
                "updated_time": "2025-12-12T10:00:00Z",
                "labels": ["代码", "审查"],
                "is_public": true,
                "variables": [
                    {"field_name": "code", "field_value": ""},
                    {"field_name": "name", "field_value": ""}
                ]
            }
        ]
    """
    # Mock 模式：返回 mock 数据
    if settings.BKAIDEV_USE_MOCK:
        logger.info("BKAIDEV_USE_MOCK is enabled, returning mock data for fetch_prompts_list")
        return _get_mock_prompts_by_keyword(keyword)

    url_prefix = _get_bkaidev_url_prefix()
    if not url_prefix:
        logger.warning("BKAIDEV_URL_PREFIX is not configured, return empty list")
        return []

    url = url_join(url_prefix, "/api/v1/prompts/")
    headers = gen_gateway_headers()
    # 添加用户信息到请求头
    headers["X-Bk-Username"] = username

    data = {}
    if keyword:
        data["keyword"] = keyword

    ok, resp_data = http_get(url, data, headers=headers, timeout=settings.BKAIDEV_API_TIMEOUT)
    if not ok:
        logger.error(
            "bkaidev api failed! %s %s, data: %s, request_id: %s, error: %s",
            "http_get",
            url,
            data,
            local.request_id,
            resp_data.get("error", ""),
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request bkaidev fail! "
            f"Request=[http_get {urlparse(url).path} request_id={local.request_id}] "
            f"error={resp_data.get('error', '')}"
        )

    # 根据 BKAIDev 平台的实际响应格式进行解析
    # 假设响应格式为: {"result": true, "data": [...], "message": ""}
    if isinstance(resp_data, dict):
        return resp_data.get("data", [])
    if isinstance(resp_data, list):
        return resp_data

    return []


def fetch_prompts_by_ids(prompt_ids: List[str]) -> List[Dict[str, Any]]:
    """
    根据 prompt IDs 从 BKAIDev 平台批量获取 prompts 详情

    Args:
        prompt_ids: prompt ID 列表

    Returns:
        prompts 详情列表
    """
    if not prompt_ids:
        return []

    # Mock 模式：返回 mock 数据
    if settings.BKAIDEV_USE_MOCK:
        logger.info("BKAIDEV_USE_MOCK is enabled, returning mock data for fetch_prompts_by_ids")
        return _get_mock_prompts_by_ids(prompt_ids)

    url_prefix = _get_bkaidev_url_prefix()
    if not url_prefix:
        logger.warning("BKAIDEV_URL_PREFIX is not configured, return empty list")
        return []

    url = url_join(url_prefix, "/api/v1/prompts/batch/")
    headers = gen_gateway_headers()

    data = {
        "ids": prompt_ids,
    }

    ok, resp_data = http_post(url, data, headers=headers, timeout=settings.BKAIDEV_API_TIMEOUT)
    if not ok:
        logger.error(
            "bkaidev api failed! %s %s, data: %s, request_id: %s, error: %s",
            "http_post",
            url,
            data,
            local.request_id,
            resp_data.get("error", ""),
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request bkaidev fail! "
            f"Request=[http_post {urlparse(url).path} request_id={local.request_id}] "
            f"error={resp_data.get('error', '')}"
        )

    # 根据 BKAIDev 平台的实际响应格式进行解析
    if isinstance(resp_data, dict):
        return resp_data.get("data", [])
    if isinstance(resp_data, list):
        return resp_data

    return []


def fetch_prompts_updated_time(prompt_ids: List[str]) -> Dict[str, str]:
    """
    从 BKAIDev 平台批量获取 prompts 的更新时间

    Args:
        prompt_ids: prompt ID 列表

    Returns:
        prompt_id -> updated_time 的映射
        例如: {"prompt_001": "2025-12-12T10:00:00Z", "prompt_002": "2025-12-11T15:30:00Z"}
    """
    if not prompt_ids:
        return {}

    # Mock 模式：返回 mock 数据
    if settings.BKAIDEV_USE_MOCK:
        logger.info("BKAIDEV_USE_MOCK is enabled, returning mock data for fetch_prompts_updated_time")
        return _get_mock_prompts_updated_time(prompt_ids)

    url_prefix = _get_bkaidev_url_prefix()
    if not url_prefix:
        logger.warning("BKAIDEV_URL_PREFIX is not configured, return empty dict")
        return {}

    url = url_join(url_prefix, "/api/v1/prompts/updated-time/")
    headers = gen_gateway_headers()

    data = {
        "ids": prompt_ids,
    }

    ok, resp_data = http_post(url, data, headers=headers, timeout=settings.BKAIDEV_API_TIMEOUT)
    if not ok:
        logger.error(
            "bkaidev api failed! %s %s, data: %s, request_id: %s, error: %s",
            "http_post",
            url,
            data,
            local.request_id,
            resp_data.get("error", ""),
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request bkaidev fail! "
            f"Request=[http_post {urlparse(url).path} request_id={local.request_id}] "
            f"error={resp_data.get('error', '')}"
        )

    # 根据 BKAIDev 平台的实际响应格式进行解析
    # 假设响应格式为: {"result": true, "data": {"prompt_001": "2025-12-12T10:00:00Z", ...}, "message": ""}
    if isinstance(resp_data, dict):
        data_result = resp_data.get("data", {})
        if isinstance(data_result, dict):
            return data_result
        # 如果 data 是列表格式，转换为字典
        if isinstance(data_result, list):
            return {item.get("id"): item.get("updated_time", "") for item in data_result if item.get("id")}

    return {}
