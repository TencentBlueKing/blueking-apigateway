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
from typing import Dict, Optional

from apigateway.biz.access_log.log_search import LogSearchClient

logger = logging.getLogger(__name__)


def search_gateway_log(request_id: str, gateway_type: str = "upstream") -> Optional[Dict]:
    """通过 request_id 查询网关日志

    bk-apigateway 的 access_log ES 中，request_id 字段对应的是 X-Bkapi-Request-ID，
    而这个值就是 mcp-proxy 日志中的 request_id 字段（从上游传入的）。

    Args:
        request_id: 网关的请求 ID
        gateway_type: 网关类型，"upstream" 或 "downstream"
    """
    if not request_id:
        logger.warning("search_gateway_log called with empty request_id, gateway_type=%s", gateway_type)
        return None

    try:
        # 使用已有的 access_log LogSearchClient 查询
        # 注意：这里查询的是 bk-apigateway 的日志索引
        # 对于 upstream（bk-apigateway），request_id 是直接对应的
        # 对于 downstream（biz-gateway），如果它的日志也在同一个 ES 索引中，才能查询到
        logger.debug(
            "searching %s gateway log with request_id=%s",
            gateway_type,
            request_id,
        )
        client = LogSearchClient(request_id=request_id, time_range=7 * 24 * 60 * 60)  # 7天
        total_count, logs = client.search_logs(offset=0, limit=1)
        logger.debug(
            "%s gateway log search result: request_id=%s, total_count=%s, has_logs=%s",
            gateway_type,
            request_id,
            total_count,
            bool(logs),
        )
        if logs:
            log = logs[0]
            return _format_gateway_log(log, gateway_type)
        logger.warning(
            "no %s gateway log found for request_id=%s, may be out of time range or not indexed",
            gateway_type,
            request_id,
        )
    except Exception:
        logger.exception(
            "failed to search %s gateway log for request_id=%s",
            gateway_type,
            request_id,
        )

    return None


def _format_gateway_log(log: Dict, gateway_type: str) -> Dict:
    """格式化网关日志"""
    # 下游网关使用实际的 backend_name 字段作为 service 名称
    service = log.get("backend_name") or "biz-gateway" if gateway_type == "downstream" else "bk-apigateway"

    return {
        "layer": "gateway",
        "service": service,
        "timestamp": log.get("timestamp"),
        "request_id": log.get("request_id"),
        "method": log.get("method"),
        "http_host": log.get("http_host"),
        "http_path": log.get("http_path"),
        "status": log.get("status"),
        "request_duration": log.get("request_duration"),
        "backend_duration": log.get("backend_duration"),
        "stage": log.get("stage"),
        "resource_name": log.get("resource_name"),
        "backend_host": log.get("backend_host"),
        "backend_path": log.get("backend_path"),
        "backend_method": log.get("backend_method"),
        "backend_scheme": log.get("backend_scheme"),
        "app_code": log.get("app_code"),
        "client_ip": log.get("client_ip"),
        "error": log.get("error"),
        "code_name": log.get("code_name"),
    }
