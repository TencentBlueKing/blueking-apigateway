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
        data = self._es_client.execute_search(s.to_dict())
        hits = data["hits"]
        return hits["total"], [self._to_log_display(hit) for hit in hits["hits"]]

    def get_time_chart(self) -> Dict:
        """查询请求量时间分布图"""
        s = self._build_date_histogram_search()
        data = self._es_client.execute_search(s.to_dict())
        return self._convert_histogram_buckets(data.get("aggregations", {}))

    def _build_base_search(self, order: Optional[bool] = None) -> Search:
        s = Search()

        # mcp-proxy 的 HTTP 层日志和 MCP 协议层日志共用同一个 ES index，
        # 通过 exists 过滤只查询 MCP 协议层日志（仅该层包含 mcp_method 字段）
        s = s.filter("exists", field="mcp_method")

        s = self._apply_term_filters(s)
        s = self._apply_conditions(s)
        s = self._apply_time_range(s)

        if order:
            s = s.sort({self._es_time_field_name: {"order": "desc"}})

        if self._query_string:
            s = s.query("query_string", query=self._query_string)

        return s

    def _apply_term_filters(self, s: Search) -> Search:
        """Apply term filters for MCP-specific fields."""
        term_fields = {
            "gateway_name": self._gateway_name,
            "mcp_server_name": self._mcp_server_name,
            "mcp_method": self._mcp_method,
            "tool_name": self._tool_name,
            "prompt_name": self._prompt_name,
            "app_code": self._app_code,
            "request_id": self._request_id,
            "x_request_id": self._x_request_id,
            "session_id": self._session_id,
            "status": self._status,
        }
        for field, value in term_fields.items():
            if value:
                s = s.filter("term", **{field: value})
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
        s = s.source(fields=MCP_SERVER_LOG_OUTPUT_FIELDS)
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

    def _to_log_display(self, hit: Dict) -> Dict:
        log = hit["_source"]
        log["timestamp"] = time_utils.convert_epoch_millisecond_to_second(hit["sort"][0])
        return log
