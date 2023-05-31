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

from apigateway.apps.monitor.constants import SOURCE_TIME_OFFSET_SECONDS
from apigateway.components.bkdata import bkdata_component


class BKDataSearchClient:
    def __init__(self, es_index, output_fields):
        self.es_index = es_index
        self.output_fields = output_fields

    def search(self, source_timestamp, match_dimension):
        """获取触发告警的事件详情，即es中记录详情"""
        must_filter = [
            {
                "range": {
                    "dtEventTimeStamp": {
                        "gte": (source_timestamp - SOURCE_TIME_OFFSET_SECONDS) * 1000,
                        "lt": (source_timestamp + SOURCE_TIME_OFFSET_SECONDS) * 1000,
                    }
                }
            }
        ]

        for key, value in match_dimension.items():
            must_filter.append({"term": {key: value}})

        sql = {
            "index": self.es_index,
            "body": {
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
            },
        }

        result, message, data = bkdata_component.get_data(prefer_storage="es", sql=json.dumps(sql))
        if not result:
            return False, message, None

        hits = data.get("list", {}).get("hits", {}).get("hits", [])  # type: ignore
        if len(hits) == 0:
            return False, "从数据平台获取数据为空", None

        return True, "", hits
