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
from operator import itemgetter
from typing import Any, Dict, Iterable, List, Optional

from bkapi.paasv3.shortcuts import get_client_by_username
from cachetools import TTLCache, cached
from django.conf import settings

from apigateway.components.handler import RequestAPIHandler
from apigateway.components.utils import inject_accept_language, inject_operation_tenant_id
from apigateway.utils.list import chunk_list

logger = logging.getLogger(__name__)


class PaaSV3Component:
    """API 网关 paasv3 相关接口"""

    def __init__(self):
        self._client = get_client_by_username(username="admin", endpoint=settings.BK_PAAS3_API_URL)
        self._client.session.register_hook("request", inject_accept_language)
        self._client.session.register_hook("request", inject_operation_tenant_id)
        self._request_handler = RequestAPIHandler("bkpaas3")

    @cached(cache=TTLCache(maxsize=2000, ttl=300))
    def get_app(self, app_code: str) -> Optional[Dict[str, Any]]:
        data = self.get_apps([app_code])
        return data.get(app_code)

    def get_apps(self, app_code_list: List[str]) -> Dict[str, Any]:
        """
        :param app_code_list: 蓝鲸应用 bk_app_code 列表
        """
        result_data = []

        # paas 限制参数 id 列表最大长度 20，因此将 app_code_list 拆分成多组
        for app_codes in chunk_list(app_code_list, n=20):
            params = {
                "private_token": getattr(settings, "BK_PAAS3_PRIVATE_TOKEN", ""),
                "id": app_codes,
                "format": "bk_std_json",
            }
            api_result, response = self._request_handler.call_api(
                self._client.api.uni_apps_query_by_id,
                data=params,
            )
            data = self._request_handler.parse_api_result(api_result, response, {"code": 0}, itemgetter("data"))
            result_data.extend(data)

        apps: Iterable[Dict] = filter(None, result_data)
        return {app["code"]: app for app in apps} or {}

    def get_app_maintainers(self, bk_app_code: str) -> List[str]:
        """获取应用负责人"""
        app = self.get_app(bk_app_code)
        if not app:
            return []

        if app.get("developers"):
            return app["developers"]

        if app.get("creator"):
            return [app["creator"]]

        return []


paasv3_component = PaaSV3Component()
