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
import logging
from typing import Any, Optional

from bkapi.paasv3.shortcuts import get_client_by_username
from bkapi_client_core.utils import to_curl
from cachetools import TTLCache, cached
from django.conf import settings
from django.utils.translation import gettext as _
from requests import Response

from apigateway.common.constants import CACHE_MAXSIZE, CacheTimeLevel
from apigateway.common.error_codes import error_codes
from apigateway.components.utils import inject_accept_language
from apigateway.utils.list import chunk_list

logger = logging.getLogger(__name__)


class PaaSV3Component:
    def __init__(self):
        self._client = get_client_by_username(username="", endpoint=settings.BK_PAAS3_API_URL)
        self._client.session.register_hook("request", inject_accept_language)

    def _parse_response(self, response: Optional[Response]) -> Any:
        if response is None:
            raise error_codes.INTERNAL.format(_("请求 bkpaas3 获取应用信息失败，请联系系统负责人处理或稍后重试。"), replace=True)

        try:
            result = response.json()
        except (TypeError, json.JSONDecodeError):
            logger.warning(
                "request bkpaas3 error, request: %s, response: %s", to_curl(response.request), response.text
            )
            raise error_codes.INTERNAL.format(_("请求 bkpaas3 获取应用信息失败，接口响应数据非 JSON 格式。"), replace=True)

        if not result["result"]:
            logger.warning(
                "request bkpaas3 error, request: %s, response: %s", to_curl(response.request), response.text
            )
            raise error_codes.INTERNAL.format(
                _("请求 bkpaas3 获取应用信息失败，{code_slug}，{message}。").format(
                    code_slug=result.get("code_slug", "Error"),
                    message=result.get("message"),
                ),
                replace=True,
            )

        return result["data"]

    @cached(cache=TTLCache(maxsize=CACHE_MAXSIZE, ttl=CacheTimeLevel.CACHE_TIME_SHORT.value))
    def get_app(self, app_code):
        data = self.get_apps([app_code])
        return data.get(app_code)

    def get_apps(self, app_code_list):
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
            response = self._client.api.uni_apps_query_by_id.request(params)
            apps = self._parse_response(response)
            result_data.extend(apps)

        return {app["code"]: app for app in filter(None, result_data)} or {}


paasv3_component = PaaSV3Component()
