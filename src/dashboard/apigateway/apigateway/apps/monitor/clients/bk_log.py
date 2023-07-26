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
from typing import List

from django.conf import settings

from apigateway.apps.monitor.constants import SOURCE_TIME_OFFSET_SECONDS
from apigateway.common.es_clients import ESClientFactory


class LogSearchClient:
    def __init__(self, es_index: str, output_fields: List[str]):
        self.es_index = es_index
        self.output_fields = output_fields
        self._es_client = ESClientFactory.get_es_client(self.es_index)
        self._es_time_field_name: str = settings.ACCESS_LOG_CONFIG["es_time_field_name"]

    def search(self, source_timestamp: int, match_dimension: dict):
        """获取触发告警的事件详情，即es中记录详情"""
        must_filter = [
            {
                "range": {
                    self._es_time_field_name: {
                        "gte": (source_timestamp - SOURCE_TIME_OFFSET_SECONDS) * 1000,
                        "lt": (source_timestamp + SOURCE_TIME_OFFSET_SECONDS) * 1000,
                    }
                }
            }
        ]

        for key, value in match_dimension.items():
            must_filter.append({"term": {key: value}})

        body = {
            "from": 0,
            "size": 1000,
            "query": {
                "bool": {
                    "must": must_filter,
                }
            },
            "_source": {
                "includes": self.output_fields,
            },
        }

        data = self._es_client.execute_search(body)
        hits = data.get("hits", {}).get("hits", [])
        if len(hits) == 0:
            return False, "从日志平台获取数据为空", None

        return True, "", hits
