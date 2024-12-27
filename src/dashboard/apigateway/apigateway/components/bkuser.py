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

from typing import Dict, List

from cachetools import TTLCache, cached
from django.conf import settings

from apigateway.common.tenant.request import gen_operation_tenant_header, gen_tenant_header
from apigateway.utils.url import url_join

from .http import http_get
from .utils import do_blueking_http_request, gen_gateway_headers


def _call_bkuser_api(http_func, path, data, more_headers=None, timeout=10) -> Dict | List:
    # 默认请求头
    headers = gen_gateway_headers()
    if more_headers:
        headers.update(more_headers)

    host = settings.BK_API_URL_TMPL.format(api_name="bkuser")

    url = url_join(host, path)

    return do_blueking_http_request("bk-user", http_func, url, data, headers, timeout)


@cached(cache=TTLCache(maxsize=100, ttl=300))
def get_tenant_list():
    url_path = "/api/v2/tenants/"

    # use the operation tenant id
    more_headers = gen_operation_tenant_header()
    return _call_bkuser_api(http_get, url_path, {}, more_headers)


@cached(cache=TTLCache(maxsize=100, ttl=300))
def query_display_names(
    tenant_id: str,
    bk_usernames: List[str],
):
    url_path = "/api/v2/display_names/"
    data = {
        "bk_usernames": bk_usernames,
    }

    # use the specific tenant_id
    more_headers = gen_tenant_header(tenant_id)

    # note: {bk_username => display_name}

    return _call_bkuser_api(http_get, url_path, data, more_headers)
