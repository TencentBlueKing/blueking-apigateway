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
import logging
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import urlparse

from cachetools import TTLCache, cached
from django.conf import settings

from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.request import gen_tenant_header
from apigateway.utils.local import local
from apigateway.utils.url import url_join

from .bkauth import get_app_info as bkauth_get_app_info
from .http import http_get
from .utils import gen_gateway_headers

logger = logging.getLogger(__name__)


def _call_paasv3_uni_apps_query_by_id(
    tenant_id: str,
    app_codes: List[str],
) -> List[Dict[str, Any]]:
    data = {
        "id": ",".join(app_codes),
    }

    headers = gen_gateway_headers()
    headers.update(gen_tenant_header(tenant_id))

    gateway_name = "bkpaas3"
    if settings.EDITION == "te":
        gateway_name = "paasv3"
    host = settings.BK_API_URL_TMPL.format(api_name=gateway_name)

    url = url_join(host, "/prod/system/uni_applications/query/by_id/")
    timeout = 10

    ok, resp_data = http_get(url, data, headers=headers, timeout=timeout)
    if not ok:
        logger.error(
            "%s api failed! %s %s, data: %s, request_id: %s, error: %s",
            "paasv3",
            "http_get",
            url,
            data,
            local.request_id,
            resp_data["error"],
        )
        raise error_codes.REMOTE_REQUEST_ERROR.format(
            f"request paasv3 fail! "
            f"Request=[http_get {urlparse(url).path} request_id={local.request_id}]"
            f"error={resp_data['error']}"
        )

    return resp_data


@cached(cache=TTLCache(maxsize=2000, ttl=300))
def get_app(tenant_id: str, app_code: str) -> Optional[Dict[str, Any]]:
    result_data = _call_paasv3_uni_apps_query_by_id(tenant_id, [app_code])
    apps: Iterable[Dict] = filter(None, result_data)

    result = {app["code"]: app for app in apps} or {}

    return result.get(app_code)


def get_app_maintainers(bk_app_code: str) -> List[str]:
    """获取应用负责人"""
    # NOTE: here we need to get maintainers from paasv3
    #       but the X-Bk-Tenant-Id required
    #       so, we query it from bkauth first
    info = bkauth_get_app_info(bk_app_code)
    tenant_id = info["tenant_id"]

    app = get_app(tenant_id, bk_app_code)
    if not app:
        return []

    if app.get("developers"):
        return app["developers"]

    if app.get("creator"):
        return [app["creator"]]

    return []
