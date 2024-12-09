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

from typing import Dict, List, Tuple

from django.conf import settings

from apigateway.utils.local import local
from apigateway.utils.url import url_join

from .http import http_get
from .utils import do_legacy_blueking_http_request


def _call_bkauth_api(http_func, path, data, timeout=10):
    # 默认请求头
    headers = {
        "Content-Type": "application/json",
        "X-Request-Id": local.request_id,
        "X-Bk-App-Code": settings.BK_APP_CODE,
        "X-Bk-App-Secret": settings.BK_APP_SECRET,
    }

    url = url_join(settings.BK_AUTH_API_URL, path)

    return do_legacy_blueking_http_request("bkauth", http_func, url, data, headers, timeout)


def get_app_info(app_code: str) -> Dict:
    url_path = f"/api/v1/apps/{app_code}"

    return _call_bkauth_api(http_get, url_path, {})


def list_apps_of_tenant(
    tenant_mode: str, tenant_id: str, page: int = 1, page_size: int = 100
) -> Tuple[int, List[Dict]]:
    url_path = "/api/v1/apps"
    data = {
        "tenant_mode": tenant_mode,
        "page": page,
        "page_size": page_size,
    }
    if tenant_id:
        data["tenant_id"] = tenant_id

    result = _call_bkauth_api(http_get, url_path, data)
    return result["count"], result["results"]


def list_all_apps_of_tenant(tenant_mode: str, tenant_id: str) -> List[Dict]:
    page_size = 100

    # get first page
    count1, results1 = list_apps_of_tenant(tenant_mode, tenant_id, page=1, page_size=page_size)
    if count1 <= page_size:
        return results1

    all_results = []
    all_results.extend(results1)

    # get the rest pages
    rest_pages = (count1 + page_size - 1) // page_size
    for page in range(2, rest_pages + 1):
        _, results = list_apps_of_tenant(tenant_mode, tenant_id, page=page, page_size=page_size)
        all_results.extend(results)

    return all_results
