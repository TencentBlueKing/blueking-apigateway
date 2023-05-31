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
from math import nan
from typing import Any, Dict, List, Text, Tuple

from django.conf import settings
from pydantic import BaseModel

from apigateway.common.error_codes import error_codes
from apigateway.utils.http import http_get

from .component import BaseComponent

PROMETHEUS_API_TIMEOUT = 30


class RequestResult(BaseModel):
    status: Text = ""
    data: Dict[Text, Any] = {}
    error: Text = ""


class InstantVector(BaseModel):
    metric: Dict[Text, Text] = {}
    value: Tuple[float, Text] = (nan, "NaN")


class RangeVector(BaseModel):
    metric: Dict[Text, Text] = {}
    values: List[Tuple[float, Text]] = []


class QueryResult(BaseModel):
    result: List[InstantVector] = []


class QueryRangeResult(BaseModel):
    result: List[RangeVector] = []


class PrometheusComponent(BaseComponent):

    HOST = getattr(settings, "BCS_THANOS_URL", "")

    def parse_response(self, http_ok, resp):
        if not (http_ok and resp):
            return False, "", None

        result = RequestResult(**resp)
        return result.status == "success", result.error, result.data

    def _call_api(self, http_func, path, data, **kwargs):
        # TODO: _call_api 更改了父类的协议，
        # components 内部逻辑统一调整 1 使用 dynatic 封装响应，2 出错抛出异常，方法直接返回需要的数据
        ok, message, data = super()._call_api(
            http_func,
            path,
            data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
            timeout=PROMETHEUS_API_TIMEOUT,
            auth=(getattr(settings, "BCS_THANOS_USER", ""), getattr(settings, "BCS_THANOS_PASSWD", "")),
        )

        if not ok:
            raise error_codes.COMPONENT_ERROR.format(message)

        return data

    def query_range(self, query, start, end, step):
        params = {
            "query": query,
            "start": start,
            "end": end,
            "step": step,
            "timeout": PROMETHEUS_API_TIMEOUT,
        }
        data = self._call_api(
            http_get,
            "/api/v1/query_range",
            params,
        )
        return QueryRangeResult(**data)

    def query(self, query, time):
        params = {
            "query": query,
            "time": time,
            "timeout": PROMETHEUS_API_TIMEOUT,
        }
        data = self._call_api(
            http_get,
            "/api/v1/query",
            params,
        )
        return QueryResult(**data)


prometheus_component = PrometheusComponent()
