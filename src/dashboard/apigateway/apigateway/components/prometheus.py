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
from operator import itemgetter
from typing import Any, Dict

from bkapi_client_core.apigateway import OperationGroup
from bkapi_client_core.apigateway.django_helper import get_client_by_username as get_client_by_username_for_apigateway
from django.conf import settings

from apigateway.components.bkapi_client.bkmonitorv3 import Client as BkMonitorV3Client
from apigateway.components.esb_components import get_client_by_username as get_client_by_username_for_esb
from apigateway.components.handler import RequestAPIHandler


class PrometheusComponent:
    def __init__(self):
        self._api_client: OperationGroup = self._get_api_client()
        self._request_handler = RequestAPIHandler("bkmonitorv3")

    def query_range(self, bk_biz_id: str, promql: str, start: int, end: int, step: str) -> Dict[str, Any]:
        """
        Evaluate an expression query over a range of time

        :param bk_biz_id: business ID
        :param promql: prometheus query language
        :param start: start timestamp, e.g. 1622009400
        :param end: end timestamp, e.g. 1622009500
        :param step: step, e.g. "1m"
        """
        return self._promql_query(bk_biz_id, promql, start, end, step, "range")

    def query(self, bk_biz_id: str, promql: str, time_: int) -> Dict[str, Any]:
        """
        Evaluate an instant query at a single point in time

        :param bk_biz_id: business ID
        :param promql: prometheus query language
        :param time_: evaluation timestamp, e.g. 1622009400
        """
        # Instant query, no need for start, step,
        # but the backend does not allow the value to be null, so set a default value.
        # step: set to 1m, backend use it to calculate real evaluation timestamp
        return self._promql_query(bk_biz_id, promql, 0, time_, "1m", "instant")

    def _promql_query(
        self, bk_biz_id: str, promql: str, start: int, end: int, step: str, type_: str
    ) -> Dict[str, Any]:
        """
        Common query Prometheus data interface

        :param type_: choices: range, instant
            - range: corresponds to Prometheus /api/v1/query_range
            - instant: corresponds to Prometheus /api/v1/query
        """
        data = {
            "bk_biz_id": bk_biz_id,
            "promql": promql,
            "start_time": start,
            "end_time": end,
            "step": step,
            "format": "time_series",
            "type": type_,
        }

        headers = {"X-Bk-Scope-Space-Uid": f"bkcc__{bk_biz_id}"}

        api_result, response = self._request_handler.call_api(self._api_client.promql_query, data, headers=headers)
        return self._request_handler.parse_api_result(api_result, response, {"code": 200}, itemgetter("data"))

    def _get_api_client(self) -> OperationGroup:
        # use gateway: bkmonitorv3
        if settings.USE_BKAPI_BKMONITORV3:
            apigw_client = get_client_by_username_for_apigateway(BkMonitorV3Client, username="admin")
            return apigw_client.api

        # use esb api
        esb_client = get_client_by_username_for_esb("admin")
        return esb_client.monitor_v3


prometheus_component = PrometheusComponent()
