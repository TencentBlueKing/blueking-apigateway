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
from typing import Any

from django.conf import settings

from apigateway.common.tenant.request import gen_operation_tenant_headers
from apigateway.utils.url import url_join

from .http import http_post
from .utils import do_legacy_blueking_http_request


def query_range(bk_biz_id: str, promql: str, start: int, end: int, step: str) -> Any:
    """
    Evaluate an expression query over a range of time

    :param bk_biz_id: business ID
    :param promql: prometheus query language
    :param start: start timestamp, e.g. 1622009400
    :param end: end timestamp, e.g. 1622009500
    :param step: step, e.g. "1m"
    """
    return _promql_query(bk_biz_id, promql, start, end, step, "range")


def query(bk_biz_id: str, promql: str, time_: int) -> Any:
    """
    Evaluate an instant query at a single point in time

    :param bk_biz_id: business ID
    :param promql: prometheus query language
    :param time_: evaluation timestamp, e.g. 1622009400
    """
    # Instant query, no need for start, step,
    # but the backend does not allow the value to be null, so set a default value.
    # step: set to 1m, backend use it to calculate real evaluation timestamp
    return _promql_query(bk_biz_id, promql, 0, time_, "1m", "instant")


def _promql_query(bk_biz_id: str, promql: str, start: int, end: int, step: str, type_: str) -> Any:
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

    headers = {
        "X-Bk-Scope-Space-Uid": f"bkcc__{bk_biz_id}",
    }
    headers.update(gen_operation_tenant_headers())

    host = settings.BK_API_URL_TMPL.format(api_name="bkmonitorv3")

    url = url_join(host, "/prod/promql_query/")
    timeout = 30

    # FIXME: {"code": 200} as ok response should be tested
    return do_legacy_blueking_http_request("bkmonitorv3", http_post, url, data, headers, timeout)
