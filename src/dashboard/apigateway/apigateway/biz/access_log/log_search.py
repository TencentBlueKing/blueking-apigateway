#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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

from apigateway.biz.access_log.constants import ES_OUTPUT_FIELDS
from apigateway.common.es.clients import BKLogESClient
from apigateway.utils import time as time_utils
from apigateway.utils.time import SmartTimeRange

logger = logging.getLogger(__name__)


class LogSearchClient:
    _es_index: str = settings.ACCESS_LOG_CONFIG["es_index"]
    _es_time_field_name: str = settings.ACCESS_LOG_CONFIG["es_time_field_name"]

    def __init__(
        self,
        gateway_id: Optional[int] = None,
        stage_name: Optional[str] = None,
        resource_id: Optional[int] = None,
        request_id: Optional[str] = None,
        query: Optional[str] = None,
        include_conditions: Optional[List[Tuple[str, str]]] = None,
        exclude_conditions: Optional[List[Tuple[str, str]]] = None,
        time_start: Optional[int] = None,
        time_end: Optional[int] = None,
        time_range: Optional[int] = None,
    ):
        self._gateway_id = gateway_id
        self._stage_name = stage_name
        self._resource_id = resource_id
        self._request_id = request_id
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
        """
        查询日志列表

        :param offset: 偏移量
        :param limit: 查询数据量，limit 为 None 表示 offset 偏移量后的全部数据
        """
        s = self._build_logs_search(offset=offset, limit=limit, order=True)
        data = self._es_client.execute_search(s.to_dict())
        hits = data["hits"]
        return hits["total"], [self._to_log_display(hit) for hit in hits["hits"]]

    def get_time_chart(self) -> Dict:
        """
        查询请求量图例

        :return: series 为时间点对应的数据个数，timeline 为时间点对应的时间戳
            {
                "series": [3, 5, 20],
                "timeline": [1690330800, 1690330860, 1690330920]
            }
        """
        s = self._build_date_histogram_search()
        data = self._es_client.execute_search(s.to_dict())
        return self._convert_histogram_buckets(data.get("aggregations", {}))

    def _build_base_search(self, order: Optional[bool] = None) -> Search:
        s = Search()

        if self._gateway_id:
            s = s.filter("term", api_id=self._gateway_id)

        if self._stage_name:
            s = s.filter("term", stage=self._stage_name)

        if self._resource_id:
            s = s.filter("term", resource_id=self._resource_id)

        if self._request_id:
            s = s.filter("term", request_id=self._request_id)

        if self._include_conditions:
            for key, val in self._include_conditions:
                s = s.filter("term", **{key: val})

        if self._exclude_conditions:
            for key, val in self._exclude_conditions:
                s = s.exclude("term", **{key: val})

        # time range
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

        if order:
            s = s.sort({self._es_time_field_name: {"order": "desc"}})

        if self._query_string:
            # 不能添加 fields 参数，如果 fields 中包含整数字段，查询会失败
            s = s.query("query_string", query=self._query_string)

        return s

    def _build_logs_search(self, offset: int = 0, limit: Optional[int] = None, order: Optional[bool] = None) -> Search:
        s = self._build_base_search(order=order)
        s = s.source(fields=ES_OUTPUT_FIELDS)
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
            # min_doc_count=0，extended_bounds 强制返回空数据，时间间隔内缺少数据时，则自动补充 0，使存在空数据时，图例时间范围完整
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
