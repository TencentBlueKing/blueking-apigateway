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
from typing import Dict, List, Optional, Tuple

from django.conf import settings
from elasticsearch_dsl import Search
from elasticsearch_dsl.aggs import A

from apigateway.service.es.clients import BKLogESClient
from apigateway.utils import time as time_utils
from apigateway.utils.time import SmartTimeRange

from .constants import MCP_SERVER_LOG_OUTPUT_FIELDS

logger = logging.getLogger(__name__)


class MCPServerLogSearchClient:
    """MCP Server 日志搜索客户端

    查询 mcp-proxy LoggingMiddleware 输出到 ES 的访问日志。
    """

    _es_index: str = settings.MCP_SERVER_ACCESS_LOG_CONFIG["es_index"]
    _es_time_field_name: str = settings.MCP_SERVER_ACCESS_LOG_CONFIG["es_time_field_name"]

    def __init__(
        self,
        gateway_name: Optional[str] = None,
        gateway_id: Optional[int] = None,
        mcp_server_name: Optional[str] = None,
        mcp_method: Optional[str] = None,
        tool_name: Optional[str] = None,
        prompt_name: Optional[str] = None,
        app_code: Optional[str] = None,
        request_id: Optional[str] = None,
        x_request_id: Optional[str] = None,
        session_id: Optional[str] = None,
        status: Optional[str] = None,
        query: Optional[str] = None,
        include_conditions: Optional[List[Tuple[str, str]]] = None,
        exclude_conditions: Optional[List[Tuple[str, str]]] = None,
        time_start: Optional[int] = None,
        time_end: Optional[int] = None,
        time_range: Optional[int] = None,
    ):
        self._gateway_name = gateway_name
        self._gateway_id = gateway_id
        self._mcp_server_name = mcp_server_name
        self._mcp_method = mcp_method
        self._tool_name = tool_name
        self._prompt_name = prompt_name
        self._app_code = app_code
        self._request_id = request_id
        self._x_request_id = x_request_id
        self._session_id = session_id
        self._status = status
        self._query_string = query
        self._include_conditions = include_conditions
        self._exclude_conditions = exclude_conditions

        self._smart_time_range: Optional[SmartTimeRange] = None

        if (time_start and time_end) or time_range:
            self._smart_time_range = SmartTimeRange(
                time_start=time_start,
                time_end=time_end,
                time_range=time_range,
            )

        self._es_client = BKLogESClient(self._es_index)

    def search_logs(self, offset: int = 0, limit: Optional[int] = None) -> Tuple[int, List[Dict]]:
        """查询 MCP Server 日志列表"""
        s = self._build_logs_search(offset=offset, limit=limit, order=True)
        query_dict = s.to_dict()
        logger.debug("MCPServerLogSearchClient search_logs query: %s", query_dict)
        data = self._es_client.execute_search(query_dict)
        hits = data["hits"]
        logger.debug(
            "MCPServerLogSearchClient search_logs result: total=%s, hits_count=%s", hits["total"], len(hits["hits"])
        )
        return hits["total"], [self._to_log_display(hit) for hit in hits["hits"]]

    def get_time_chart(self) -> Dict:
        """查询请求量时间分布图"""
        s = self._build_date_histogram_search()
        data = self._es_client.execute_search(s.to_dict())
        return self._convert_histogram_buckets(data.get("aggregations", {}))

    def _build_base_search(self, order: Optional[bool] = None) -> Search:
        s = Search()

        # mcp-proxy 的 HTTP 层日志和 MCP 协议层日志共用同一个 ES index，
        # 同时展示 HTTP 层和 MCP 协议层日志，不再强制要求 mcp_method 字段存在

        # 使用 gateway_id 做精确过滤（与普通网关日志 LogSearchClient 对齐，使用整数 term 查询）
        if self._gateway_id:
            s = s.filter("term", gateway_id=self._gateway_id)

        s = self._apply_term_filters(s)
        s = self._apply_conditions(s)
        s = self._apply_time_range(s)

        if order:
            s = s.sort({self._es_time_field_name: {"order": "desc"}})

        if self._query_string:
            s = s.query("query_string", query=self._query_string)

        return s

    def _apply_term_filters(self, s: Search) -> Search:
        """Apply term filters for MCP-specific fields.

        注意：HTTP 层日志的部分字段（如 gateway_name, mcp_server_name, method, path 等）
        存储在 __ext_json 中而非顶层。对于这些字段，需要同时搜索顶层和 __ext_json 嵌套路径。

        gateway_name 不在此处过滤，因为已通过 gateway_id（整数，总在顶层）做精确过滤。
        """
        # 只过滤 MCP 协议层字段（这些字段在 MCP 层日志中位于顶层）
        term_fields = {
            "mcp_method": self._mcp_method,
            "tool_name": self._tool_name,
            "prompt_name": self._prompt_name,
            "app_code": self._app_code,
            "request_id": self._request_id,
            "x_request_id": self._x_request_id,
            "session_id": self._session_id,
            "status": self._status,
        }
        # mcp_server_name 可能在顶层（MCP 协议层）或 __ext_json 中（HTTP 层），
        # 需要用 should 同时搜索两个位置
        # 注意：必须用 term 精确匹配，match 会分词导致 "bk-apigateway-prod-context"
        # 被拆成 bk/apigateway/prod/context 多个 token，筛选失效
        if self._mcp_server_name:
            from elasticsearch_dsl import Q  # noqa: PLC0415

            s = s.filter(
                "bool",
                should=[
                    Q("term", mcp_server_name=self._mcp_server_name),
                    Q("term", **{"__ext_json.mcp_server_name": self._mcp_server_name}),
                ],
                minimum_should_match=1,
            )

        applied_filters = {}
        for field, value in term_fields.items():
            if value:
                s = s.filter("term", **{field: value})
                applied_filters[field] = value
        if applied_filters:
            logger.debug("MCPServerLogSearchClient applied term filters: %s", applied_filters)
        return s

    def _apply_conditions(self, s: Search) -> Search:
        """Apply include/exclude conditions."""
        if self._include_conditions:
            for key, val in self._include_conditions:
                s = s.filter("term", **{key: val})

        if self._exclude_conditions:
            for key, val in self._exclude_conditions:
                s = s.exclude("term", **{key: val})

        return s

    def _apply_time_range(self, s: Search) -> Search:
        """Apply time range filter."""
        if self._smart_time_range:
            time_start, time_end = self._smart_time_range.get_head_and_tail()
            s = s.filter(
                "range",
                **{
                    self._es_time_field_name: {
                        "gte": time_utils.convert_second_to_epoch_millisecond(time_start),
                        "lte": time_utils.convert_second_to_epoch_millisecond(time_end),
                    }
                },
            )
        return s

    def _build_logs_search(self, offset: int = 0, limit: Optional[int] = None, order: Optional[bool] = None) -> Search:
        s = self._build_base_search(order=order)
        # 除了业务字段，还需取回 __ext_json 用于合并 HTTP 层字段
        source_fields = list(MCP_SERVER_LOG_OUTPUT_FIELDS)
        if "__ext_json" not in source_fields:
            source_fields.append("__ext_json")
        s = s.source(fields=source_fields)
        if limit is None:
            return s[offset:]
        return s[offset : offset + limit]

    def _build_date_histogram_search(self) -> Search:
        assert self._smart_time_range

        s = self._build_base_search()
        start, end = self._smart_time_range.get_head_and_tail()
        aggs_by_dh = A(
            "date_histogram",
            field=self._es_time_field_name,
            fixed_interval=self._smart_time_range.get_interval(),
            min_doc_count=0,
            extended_bounds={
                "min": time_utils.convert_second_to_epoch_millisecond(start),
                "max": time_utils.convert_second_to_epoch_millisecond(end),
            },
        )
        s.aggs.bucket("histogram", aggs_by_dh)

        return s[:0]

    def _convert_histogram_buckets(self, data: Dict) -> Dict:
        timeline = []
        series = []
        buckets = data.get("histogram", {}).get("buckets", [])
        for bucket in buckets:
            ts = bucket["key"]
            timeline.append(time_utils.convert_epoch_millisecond_to_second(ts))
            series.append(bucket["doc_count"])

        return {
            "series": series,
            "timeline": timeline,
        }

    # __ext_json 中的业务字段应优先覆盖顶层同名字段。
    # 原因：Filebeat 在顶层写入的 path 是日志文件路径（如 /app/logs/mcp_proxy_api.log），
    # 而 __ext_json.path 才是真正的 HTTP 请求路径（如 /bk-apigateway-prod-context/mcp）。
    # 类似的字段还有 method、gateway_name 等。
    _EXT_JSON_OVERRIDE_FIELDS = frozenset({"path", "method", "gateway_name", "mcp_server_name"})

    def _to_log_display(self, hit: Dict) -> Dict:
        log = hit["_source"]
        log["timestamp"] = time_utils.convert_epoch_millisecond_to_second(hit["sort"][0])

        # 合并 __ext_json 中的字段到顶层
        # Go logger 输出的完整字段存储在 __ext_json 中，需要合并到顶层才能正常展示。
        # 合并策略：
        #   1. __ext_json 中的 None 值跳过（无意义）
        #   2. _EXT_JSON_OVERRIDE_FIELDS 中的字段始终覆盖（顶层可能是 Filebeat 写入的无关数据）
        #   3. 其他字段：顶层为 None 时用 __ext_json 的值填充（包括空字符串和零值，
        #      因为它们表示"字段存在但无值"，比 null 更有意义）
        ext_json = log.get("__ext_json", {}) or {}
        if ext_json:
            for key, value in ext_json.items():
                if value is None:
                    continue
                # 优先覆盖字段：__ext_json 中的值始终优先（顶层值可能是 Filebeat 写入的无关数据）
                if key in self._EXT_JSON_OVERRIDE_FIELDS or key not in log or log.get(key) is None:
                    log[key] = value

        return log
