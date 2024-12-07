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

from cachetools import TTLCache, cached
from django.conf import settings
from django.utils.translation import get_language

from apigateway.common.constants import TENANT_ID_OPERATION
from apigateway.utils.list import chunk_list
from apigateway.utils.url import url_join

from .http import http_get
from .utils import do_legacy_blueking_http_request

logger = logging.getLogger(__name__)


@cached(cache=TTLCache(maxsize=2000, ttl=300))
def get_app(app_code: str) -> Optional[Dict[str, Any]]:
    data = get_apps([app_code])
    return data.get(app_code)


def get_apps(app_code_list: List[str]) -> Dict[str, Any]:
    """
    :param app_code_list: 蓝鲸应用 bk_app_code 列表
    """
    result_data = []

    # paas 限制参数 id 列表最大长度 20，因此将 app_code_list 拆分成多组
    for app_codes in chunk_list(app_code_list, n=20):
        data = _call_paasv3_uni_apps_query_by_id(app_codes)
        result_data.extend(data)

    apps: Iterable[Dict] = filter(None, result_data)
    return {app["code"]: app for app in apps} or {}


def get_app_maintainers(bk_app_code: str) -> List[str]:
    """获取应用负责人"""
    app = get_app(bk_app_code)
    if not app:
        return []

    if app.get("developers"):
        return app["developers"]

    if app.get("creator"):
        return [app["creator"]]

    return []


def _call_paasv3_uni_apps_query_by_id(app_codes: List[str]):
    data = {
        "private_token": getattr(settings, "BK_PAAS3_PRIVATE_TOKEN", ""),
        "id": app_codes,
        "format": "bk_std_json",
    }

    headers = {
        "Content-Type": "application/json",
        "X-Bk-Tenant-Id": TENANT_ID_OPERATION,
    }
    language = get_language()
    if language:
        headers["Accept-Language"] = language

    url = url_join(settings.BK_PAAS3_API_URL, "/prod/system/uni_applications/query/by_id/")
    timeout = 10

    return do_legacy_blueking_http_request("bklog", http_get, url, data, headers, timeout)
