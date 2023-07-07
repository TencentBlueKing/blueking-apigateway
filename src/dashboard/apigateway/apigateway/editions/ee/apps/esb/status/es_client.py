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
"""
请求Elasticsearch辅助Client
"""
from typing import ClassVar, Type

from django.conf import settings

from apigateway.apps.access_log.constants import ESClientTypeEnum
from apigateway.apps.access_log.es_clients import BaseESClient, BKLogESClient, RawESClient


class BaseSearchClient:
    _es_index = settings.BK_ESB_ACCESS_LOG_CONFIG["es_index"]
    _es_time_field_name = settings.BK_ESB_ACCESS_LOG_CONFIG["es_time_field_name"]
    _es_client_class: ClassVar[Type[BaseESClient]]

    def __init__(self):
        self._es_client = self._es_client_class(self._es_index)

    def search_esb_api_log(self, body):
        raise NotImplementedError

    def get_system_stats(self, time_since=None, system_name=None, mts_start=None, mts_end=None):
        if mts_start and mts_end:
            term_filter = {"range": {self._es_time_field_name: {"gte": mts_start, "lte": mts_end}}}
        else:
            term_filter = {"range": {self._es_time_field_name: {"gte": "now-%s" % time_since}}}

        query_dict = {
            "bool": {
                "filter": {
                    "bool": {
                        "must": [
                            {"term": {"type": "pyls-comp-api"}},
                            term_filter,
                        ]
                    },
                }
            }
        }
        if system_name:
            query_dict["bool"]["filter"]["bool"]["must"].append({"term": {"req_system_name": system_name}})

        body = {
            "size": 0,
            "timeout": f"{settings.DEFAULT_ES_SEARCH_TIMEOUT}s",
            "query": query_dict,
            "aggs": {
                "systems": {
                    "terms": {
                        "field": "req_system_name",
                        "size": settings.DEFAULT_ES_AGGS_TERM_SIZE,
                    },
                    "aggs": {
                        "error_count": {"filter": {"exists": {"field": "req_exception"}}},
                        "avg_resp_time": {"avg": {"field": "req_msecs_cost"}},
                        "resp_time_outlier": {"percentiles": {"field": "req_msecs_cost"}},
                    },
                }
            },
        }
        return self.search_esb_api_log(body=body)

    def get_sys_events_timeline(self, last_db_ts_happened_at, time_interval_seconds, time_interval):
        term_filter = {
            "range": {self._es_time_field_name: {"gt": int((last_db_ts_happened_at + time_interval_seconds) * 1000)}}
        }
        query_dict = {
            "bool": {
                "filter": {
                    "bool": {
                        "must": [
                            {"term": {"type": "pyls-comp-api"}},
                            term_filter,
                        ]
                    },
                }
            }
        }

        body = {
            "size": 0,
            "timeout": f"{settings.DEFAULT_ES_SEARCH_TIMEOUT}s",
            "query": query_dict,
            "aggs": {
                "systems": {
                    "terms": {
                        "field": "req_system_name",
                        "size": settings.DEFAULT_ES_AGGS_TERM_SIZE,
                    },
                    "aggs": {
                        "requests_over_time": {
                            "date_histogram": {"field": self._es_time_field_name, "interval": time_interval},
                            "aggs": {
                                "error_count": {"filter": {"exists": {"field": "req_exception"}}},
                                "avg_resp_time": {"avg": {"field": "req_msecs_cost"}},
                                "resp_time_outlier": {"percentiles": {"field": "req_msecs_cost"}},
                            },
                        }
                    },
                }
            },
        }
        return self.search_esb_api_log(body=body)

    def get_sys_date_histogram(self, mts_start, mts_end, system_name, time_interval):
        time_filter = {"range": {self._es_time_field_name: {"gte": mts_start, "lte": mts_end}}}

        body = {
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "must": [
                                {"term": {"type": "pyls-comp-api"}},
                                {"term": {"req_system_name": system_name}},
                                time_filter,
                            ]
                        },
                    }
                }
            },
            "aggs": {
                "systems": {
                    "terms": {"field": "req_system_name", "size": 4},
                    "aggs": {
                        "error_count": {"filter": {"exists": {"field": "req_exception"}}},
                        "avg_resp_time": {"avg": {"field": "req_msecs_cost"}},
                        "resp_time_outlier": {"percentiles": {"field": "req_msecs_cost"}},
                        "requests_over_time": {
                            "date_histogram": {
                                "field": self._es_time_field_name,
                                "interval": time_interval,
                                "min_doc_count": 0,
                                "extended_bounds": {"max": mts_end},
                            },
                            "aggs": {
                                "error_count": {"filter": {"exists": {"field": "req_exception"}}},
                                "avg_resp_time": {"avg": {"field": "req_msecs_cost"}},
                                "resp_time_outlier": {"percentiles": {"field": "req_msecs_cost"}},
                            },
                        },
                    },
                }
            },
        }
        return self.search_esb_api_log(body=body)

    def get_sys_details_group_by(self, mts_start, mts_end, time_since, system_name, group_by):
        if mts_start and mts_end:
            term_filter = {"range": {self._es_time_field_name: {"gte": mts_start, "lte": mts_end}}}
        else:
            term_filter = {"range": {self._es_time_field_name: {"gte": "now-%s" % time_since}}}

        body = {
            "size": 0,
            "timeout": f"{settings.DEFAULT_ES_SEARCH_TIMEOUT}s",
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "must": [
                                {"term": {"type": "pyls-comp-api"}},
                                {"term": {"req_system_name": system_name}},
                                term_filter,
                            ]
                        },
                    }
                }
            },
            "aggs": {
                "systems": {
                    "terms": {
                        "field": "%s" % group_by,
                        "size": settings.DEFAULT_ES_AGGS_TERM_SIZE,
                    },
                    "aggs": {
                        "error_count": {"filter": {"exists": {"field": "req_exception"}}},
                        "avg_resp_time": {"avg": {"field": "req_msecs_cost"}},
                        "resp_time_outlier": {"percentiles": {"field": "req_msecs_cost"}},
                    },
                }
            },
        }
        return self.search_esb_api_log(body=body)

    def get_sys_errors(self, mts_start, mts_end, system_name, url, app_code, component_name, size):
        query_filter = [
            {"range": {self._es_time_field_name: {"gte": mts_start, "lte": mts_end}}},
            {"term": {"type": "pyls-comp-api"}},
            {"term": {"req_system_name": system_name}},
            {"exists": {"field": "req_exception"}},
        ]

        if url:
            query_filter.append({"term": {"req_url": url}})

        if app_code:
            query_filter.append({"term": {"req_app_code": app_code}})

        if component_name:
            query_filter.append({"term": {"req_component_name": component_name}})

        body = {
            "_source": {"excludes": ["req_params", "req_response"]},
            "size": size,
            "sort": [{self._es_time_field_name: "desc"}],
            "query": {"bool": {"filter": query_filter}},
        }
        return self.search_esb_api_log(body=body)


class RawESSearchClient(BaseSearchClient):
    _es_client_class = RawESClient

    def search_esb_api_log(self, body):
        return self._es_client.execute_search(body=body)


class BKLogSearchClient(BaseSearchClient):
    """使用 BK_LOG 系统查询 ES 数据"""

    _es_client_class = BKLogESClient

    def search_esb_api_log(self, body):
        return self._es_client.execute_search(body=body)


def get_search_es_client():
    es_client_type = settings.BK_ESB_ACCESS_LOG_CONFIG["es_client_type"]
    if es_client_type == ESClientTypeEnum.BK_LOG.value:
        return BKLogSearchClient()

    elif es_client_type == ESClientTypeEnum.ELASTICSEARCH.value:
        return RawESSearchClient()

    raise ValueError(f"unsupported es_client_type: {es_client_type}")
