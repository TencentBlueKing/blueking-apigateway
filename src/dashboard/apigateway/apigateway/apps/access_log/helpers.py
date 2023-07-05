# -*- coding: utf-8 -*-
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
import json
import logging
import urllib
from abc import ABC, abstractmethod
from typing import ClassVar, Type

from django.conf import settings
from django.utils.translation import gettext as _
from elasticsearch_dsl import Search
from elasticsearch_dsl.aggs import A

from apigateway.apps.access_log.constants import (
    ES_OUTPUT_FIELDS,
    ES_QUERY_FIELDS,
    SENSITIVE_KEYS,
    SENSITIVE_KEYS_MATCH_PATTERN,
    SENSITIVE_KEYS_PART_MATCH_PATTERN,
    ESClientTypeEnum,
)
from apigateway.apps.access_log.es_clients import BaseESClient, BKDataESClient, BKLogESClient, DslESClient
from apigateway.apps.access_log.exceptions import NotScrubbedException
from apigateway.utils import time as time_utils

logger = logging.getLogger(__name__)


def get_es_client_class():
    es_client_type = settings.ACCESS_LOG_CONFIG["es_client_type"]
    return LogSearchFactory().get_client_class(es_client_type)


class LogSearchFactory:
    def get_client_class(self, es_client_type):
        if es_client_type == ESClientTypeEnum.BKDATA.value:
            return BKDataLogSearch

        elif es_client_type == ESClientTypeEnum.BK_LOG.value:
            return BKLogLogSearch

        elif es_client_type == ESClientTypeEnum.ELASTICSEARCH.value:
            return DslESLogSearch

        return ValueError(f"does not support es_client_type {es_client_type}")


class BaseLogSearch(ABC):
    _es_index: str = settings.ACCESS_LOG_CONFIG["es_index"]
    _es_time_field_name: str = settings.ACCESS_LOG_CONFIG["es_time_field_name"]
    _es_client_class: ClassVar[Type[BaseESClient]]

    # FIXME: change api_id to gateway_id
    def __init__(
        self,
        api_id=None,
        stage_name=None,
        request_id=None,
        query=None,
        time_start=None,
        time_end=None,
        time_range=None,
    ):
        self._gateway_id = api_id
        self._stage_name = stage_name
        self._request_id = request_id
        self._query_string = query
        self._smart_time_range = None

        if (time_start and time_end) or time_range:
            self._smart_time_range = time_utils.SmartTimeRange(
                time_start=time_start,
                time_end=time_end,
                time_range=time_range,
            )

        self._es_client = self._es_client_class(self._es_index)

    def _build_base_search(self, order=None, **kwargs):
        s = Search()

        if self._gateway_id:
            s = s.filter("term", api_id=self._gateway_id)

        if self._stage_name:
            s = s.filter("term", stage=self._stage_name)

        if self._request_id:
            s = s.filter("term", request_id=self._request_id)

        # time range
        if self._smart_time_range:
            time_start, time_end = self._smart_time_range.get_head_and_tail()
            s = s.filter(
                "range",
                **{
                    self._es_time_field_name: {
                        "gte": time_utils.convert_second_to_epoch_millis(time_start),
                        "lte": time_utils.convert_second_to_epoch_millis(time_end),
                    }
                },
            )

        if order:
            s = s.sort({self._es_time_field_name: {"order": "desc"}})

        if self._query_string:
            s = s.query("query_string", fields=ES_QUERY_FIELDS, query=self._query_string)

        return s

    def _build_logs_search(self, offset=0, limit=None, order=None):
        s = self._build_base_search(order=order)
        s = s.source(fields=ES_OUTPUT_FIELDS)
        if limit is None:
            return s[offset:]
        return s[offset : offset + limit]

    def _build_date_histogram_search(self):
        s = self._build_base_search()

        aggs_by_dh = A(
            "date_histogram",
            field=self._es_time_field_name,
            interval=self._smart_time_range.get_interval(),
            min_doc_count=1,
        )
        s.aggs.bucket("histogram", aggs_by_dh)

        return s[:0]

    def _convert_histogram_buckets(self, data):
        timeline = []
        series = []
        buckets = data.get("histogram", {}).get("buckets", [])
        for bucket in buckets:
            ts = bucket["key"]
            timeline.append(time_utils.convert_epoch_millis_to_second(ts))
            series.append(bucket["doc_count"])

        return {
            "series": series,
            "timeline": timeline,
        }

    @abstractmethod
    def search_logs(self, **kwargs):
        pass

    @abstractmethod
    def get_time_chart(self, **kwargs):
        pass


class DslESLogSearch(BaseLogSearch):
    _es_client_class = DslESClient

    def search_logs(self, offset=0, limit=None):
        s = self._build_logs_search(offset=offset, limit=limit, order=True)
        completed_search = self._es_client.complete_search(s)
        response = self._es_client.execute_search_with_dsl_search(completed_search)
        return completed_search.count(), [self._to_log_display(hit) for hit in response]

    def get_time_chart(self):
        data = self._search_date_histogram()
        return self._convert_histogram_buckets(data)

    def _to_log_display(self, hit):
        log = hit.to_dict()
        log["timestamp"] = time_utils.convert_epoch_millis_to_second(hit.meta.sort[0])
        return log

    def _search_date_histogram(self):
        s = self._build_date_histogram_search()
        completed_search = self._es_client.complete_search(s)
        response = self._es_client.execute_search_with_dsl_search(completed_search)
        return response.aggregations.to_dict()


class BKDataLogSearch(BaseLogSearch):
    _es_client_class = BKDataESClient

    def search_logs(self, offset=0, limit=None):
        s = self._build_logs_search(offset=offset, limit=limit, order=True)
        data = self._es_client.execute_search(s.to_dict())
        hits = data["list"]["hits"]
        return hits["total"], [self._to_log_display(hit) for hit in hits["hits"]]

    def get_time_chart(self):
        s = self._build_date_histogram_search()
        data = self._es_client.execute_search(s.to_dict())
        return self._convert_histogram_buckets(data["list"]["aggregations"])

    def _to_log_display(self, hit):
        log = hit["_source"]
        log["timestamp"] = time_utils.convert_epoch_millis_to_second(hit["sort"][0])
        return log


class BKLogLogSearch(BaseLogSearch):
    """使用蓝鲸日志平台查询日志"""

    _es_client_class = BKLogESClient

    def search_logs(self, offset=0, limit=None):
        s = self._build_logs_search(offset=offset, limit=limit, order=True)
        data = self._es_client.execute_search(s.to_dict())
        hits = data["hits"]
        return hits["total"], [self._to_log_display(hit) for hit in hits["hits"]]

    def get_time_chart(self):
        s = self._build_date_histogram_search()
        data = self._es_client.execute_search(s.to_dict())
        return self._convert_histogram_buckets(data.get("aggregations", {}))

    def _to_log_display(self, hit):
        log = hit["_source"]
        log["timestamp"] = time_utils.convert_epoch_millis_to_second(hit["sort"][0])
        return log


class DataScrubber:
    """日志中敏感信息擦除"""

    def scrub_sensitive_data(self, logs):
        for log in logs:
            if "params" in log and self._contains_sensitive_data(log["params"]):
                try:
                    log["params"] = self._scrub_urlencoded_data(log["params"])
                except NotScrubbedException:
                    log["params"] = _("因数据截断或未知数据格式，敏感数据未能过滤，数据暂不展示。")

            if "body" in log and self._contains_sensitive_data(log["body"]):
                try:
                    log["body"] = self._scrub_body(log["body"])
                except NotScrubbedException:
                    log["body"] = _("因数据截断或未知数据格式，敏感数据未能过滤，数据暂不展示。")

        return logs

    def _contains_sensitive_data(self, content):
        if not content:
            return False

        if SENSITIVE_KEYS_MATCH_PATTERN.search(content) or SENSITIVE_KEYS_PART_MATCH_PATTERN.search(content):
            return True

        return False

    def _scrub_body(self, body):
        body = body.strip()
        # json 数据
        if body.startswith("{"):
            return self._scrub_json_data(body)

        # urlencoded 数据
        if body.find("=") >= 0 and len(body.splitlines()) == 1:
            return self._scrub_urlencoded_data(body)

        raise NotScrubbedException()

    def _scrub_urlencoded_data(self, content):
        try:
            parsed_qs = urllib.parse.parse_qs(content, keep_blank_values=True, strict_parsing=True)
        except Exception:
            raise NotScrubbedException()

        scrubbed_content = self._scrub_by_keys(parsed_qs)
        return urllib.parse.urlencode(scrubbed_content, doseq=True)

    def _scrub_json_data(self, content):
        try:
            data = json.loads(content)
        except Exception:
            raise NotScrubbedException()

        scrubbed_data = self._scrub_by_keys(data)
        return json.dumps(scrubbed_data)

    def _scrub_by_keys(self, data):
        scrubbed_data = {}
        for key, value in data.items():
            if value and (key in SENSITIVE_KEYS or SENSITIVE_KEYS_PART_MATCH_PATTERN.search(key)):
                scrubbed_data[key] = "***"
            else:
                scrubbed_data[key] = value
        return scrubbed_data
