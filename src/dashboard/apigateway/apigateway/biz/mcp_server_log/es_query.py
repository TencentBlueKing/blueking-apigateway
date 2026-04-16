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
from typing import Dict, List

from elasticsearch_dsl import Search

from apigateway.biz.mcp_server_log.constants import CHAIN_OUTPUT_FIELDS
from apigateway.common.error_codes import error_codes
from apigateway.service.es.clients import BKLogESClient
from apigateway.utils import time as time_utils
from apigateway.utils.time import SmartTimeRange

logger = logging.getLogger(__name__)

# 默认时间范围（7天），避免ES查询超时或返回过多数据
_DEFAULT_TIME_RANGE_SECONDS = 7 * 24 * 60 * 60


def search_all_layers(
    es_client: BKLogESClient,
    es_time_field_name: str,
    request_id: str = "",
    x_request_id: str = "",
) -> List[Dict]:  # noqa: C901, PLR0912
    """从 ES 中查询同一 request_id 或 x_request_id 的所有层级日志"""
    s = Search()

    # 根据传入的参数决定查询条件
    if request_id:
        s = s.filter("term", request_id=request_id)
    elif x_request_id:
        s = s.filter("term", x_request_id=x_request_id)
    else:
        return []

    # 添加默认时间范围（最近7天），避免ES查询超时或返回过多数据
    # 由于request_id/x_request_id是唯一的，时间范围不会影响结果准确性
    time_range = SmartTimeRange(time_range=_DEFAULT_TIME_RANGE_SECONDS)
    time_start, time_end = time_range.get_head_and_tail()
    s = s.filter(
        "range",
        **{
            es_time_field_name: {
                "gte": time_utils.convert_second_to_epoch_millisecond(time_start),
                "lte": time_utils.convert_second_to_epoch_millisecond(time_end),
            }
        },
    )

    s = s.source(fields=CHAIN_OUTPUT_FIELDS)
    s = s.sort({es_time_field_name: {"order": "asc"}})
    s = s[:100]  # 限制最多 100 条

    try:
        data = es_client.execute_search(s.to_dict())
    except Exception as e:
        logger.exception(
            "failed to search mcp server chain logs for request_id=%s, x_request_id=%s",
            request_id,
            x_request_id,
        )
        # 重新抛出异常，让上层处理
        raise error_codes.INTERNAL.format(message=f"ES query failed: {str(e)}")

    hits = data.get("hits", {}).get("hits", [])
    logger.debug(
        "search mcp server chain logs success, request_id=%s, x_request_id=%s, hits=%s",
        request_id,
        x_request_id,
        len(hits),
    )

    return _parse_hits(hits)


def search_by_upstream_request_id(
    es_client: BKLogESClient,
    es_time_field_name: str,
    upstream_request_id: str,
) -> List[Dict]:
    """从 ES 中查询 upstream_request_id 匹配的日志

    当用户通过上游 API 返回的 request_id（即 biz-gateway 的 request_id）查询时使用。
    mcp-proxy 的 tools/call 日志中存储了 upstream_request_id 字段，
    该值是下游 API 响应中返回的 request_id。
    """
    if not upstream_request_id:
        return []

    s = Search()
    s = s.filter("term", upstream_request_id=upstream_request_id)

    # 添加默认时间范围（最近7天）
    time_range = SmartTimeRange(time_range=_DEFAULT_TIME_RANGE_SECONDS)
    time_start, time_end = time_range.get_head_and_tail()
    s = s.filter(
        "range",
        **{
            es_time_field_name: {
                "gte": time_utils.convert_second_to_epoch_millisecond(time_start),
                "lte": time_utils.convert_second_to_epoch_millisecond(time_end),
            }
        },
    )

    s = s.source(fields=CHAIN_OUTPUT_FIELDS)
    s = s.sort({es_time_field_name: {"order": "asc"}})
    s = s[:100]  # 同一 upstream_request_id 可能关联多条日志

    try:
        data = es_client.execute_search(s.to_dict())
    except Exception:
        logger.exception(
            "failed to search mcp server logs by upstream_request_id=%s",
            upstream_request_id,
        )
        return []

    hits = data.get("hits", {}).get("hits", [])
    logger.debug(
        "search mcp server logs by upstream_request_id=%s, hits=%s",
        upstream_request_id,
        len(hits),
    )

    return _parse_hits(hits, log_prefix="[upstream_request_id]")


def _parse_hits(hits: list, log_prefix: str = "") -> List[Dict]:
    """解析 ES 查询结果，提取字段并过滤无效日志"""
    result = []
    for hit in hits:
        log = hit["_source"]
        # 检查 sort 字段
        sort = hit.get("sort")
        logger.debug(
            "%s hit sort field: hit_id=%s, sort=%s, is_list=%s, len=%s",
            log_prefix,
            hit.get("_id"),
            sort,
            isinstance(sort, list),
            len(sort) if isinstance(sort, list) else "N/A",
        )
        if sort and len(sort) > 0:
            log["timestamp"] = time_utils.convert_epoch_millisecond_to_second(sort[0])
            log["timestamp_ms"] = sort[0]
            logger.debug("%s added timestamp=%s to log", log_prefix, log.get("timestamp"))
        else:
            logger.warning("%s sort field is missing or empty for hit_id=%s", log_prefix, hit.get("_id"))

        # 合并 __ext_json 中的字段到顶层（Filebeat 提取的字段）
        log = _merge_ext_json(log)

        # 清理 Filebeat 注入的日志文件路径：MCP 协议层日志（旧版本）可能没有输出 path 字段，
        # 导致顶层 path 保留了 Filebeat 写入的日志文件物理路径（如 /app/logs/mcp_proxy_api.log）。
        # 这类路径对用户无意义，应清空。
        log = _sanitize_filebeat_path(log)

        # 排除文件访问日志：如果 __ext_json.method 为空，说明是文件访问日志
        # 真正的 HTTP 请求日志有 __ext_json.method 字段
        # 但 MCP 协议层日志（audit 日志）没有 __ext_json，通过 mcp_method 字段识别
        ext_json = log.get("__ext_json", {}) or {}
        if not ext_json.get("method") and not log.get("mcp_method"):
            continue

        # 排除健康检查请求
        path = log.get("path", "")
        if "/health" in path and path.split("?")[0].split("/")[-1] == "/health":
            continue

        result.append(log)
    return result


# __ext_json 中的业务字段应优先覆盖顶层同名字段。
# 原因：Filebeat 在顶层写入的 path 是日志文件路径（如 /app/logs/mcp_proxy_api.log），
# 而 __ext_json.path 才是真正的 HTTP 请求路径（如 /bk-apigateway-prod-context/mcp）。
# 类似的字段还有 method、gateway_name 等。
_EXT_JSON_OVERRIDE_FIELDS = frozenset({"path", "method", "gateway_name", "mcp_server_name"})


def _merge_ext_json(log: Dict) -> Dict:
    """合并 __ext_json 中的字段到顶层（Filebeat 提取的字段）

    Go logger 输出的完整字段存储在 __ext_json 中，需要合并到顶层才能正常展示。
    合并策略：
      1. __ext_json 中的 None 值跳过（无意义）
      2. _EXT_JSON_OVERRIDE_FIELDS 中的字段始终覆盖（顶层可能是 Filebeat 写入的无关数据）
      3. 其他字段：顶层为 None 时用 __ext_json 的值填充（包括空字符串和零值，
         因为它们表示"字段存在但无值"，比 null 更有意义）
    """
    ext_json = log.get("__ext_json", {}) or {}
    if ext_json:
        for key, value in ext_json.items():
            if value is None:
                continue
            # 优先覆盖字段：__ext_json 中的值始终优先
            if key in _EXT_JSON_OVERRIDE_FIELDS or key not in log or log.get(key) is None:
                log[key] = value
    return log


def _sanitize_filebeat_path(log: Dict) -> Dict:
    """清理 Filebeat 注入的日志文件物理路径

    Filebeat 在采集日志时会在顶层写入 path 字段，值为日志文件的物理路径
    （如 /app/logs/mcp_proxy_api.log）。对于 HTTP 层日志，__ext_json.path 会覆盖
    该值（通过 _EXT_JSON_OVERRIDE_FIELDS）；但对于 MCP 协议层日志（旧版本未输出 path），
    Filebeat 的文件路径会残留在顶层，对用户展示无意义。

    判断逻辑：如果 path 以 .log 结尾，认为是 Filebeat 的文件路径，清空为空字符串。
    """
    path = log.get("path", "")
    if path and isinstance(path, str) and path.endswith(".log"):
        log["path"] = ""
    return log
