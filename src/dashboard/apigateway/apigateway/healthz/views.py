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

import redis
import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from requests.exceptions import HTTPError, RequestException

from apigateway.apps.access_log.helpers import get_es_client_class
from apigateway.common.error_codes import APIError
from apigateway.utils.redis_utils import get_redis_pool
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse


class CheckError(Exception):
    """检查出现错误"""


class CheckWarning(Exception):
    """检查出现警告"""


class PongView(View):
    def get(self, request):
        return HttpResponse("pong")


class HealthzView(View):
    def get(self, request):
        checkers = [
            self._check_settings,
            self._check_database,
            self._check_redis,
            # self._check_external_dependency_url,
            # self._check_bk_paasv3,
            # self._check_elasticsearch,
        ]

        for checker in checkers:
            try:
                checker()
            except CheckError as err:
                return FailJsonResponse(f"Error: {err}")
            except CheckWarning as err:
                return OKJsonResponse(f"Warning: some checks fail and do not affect core functions. {err}")

        return OKJsonResponse("OK")

    def _check_settings(self):
        """检查 django settings 配置"""
        not_allow_empty_keys = [
            # "ENCRYPT_KEY",
            "SECRET_KEY",
            "BK_APP_CODE",
            "BK_APP_SECRET",
            "BK_PAAS3_API_URL",
            "BK_COMPONENT_API_URL",
            # "BK_COMPONENT_API_INNER_URL",
        ]
        empty_keys = [key for key in not_allow_empty_keys if not getattr(settings, key, None)]
        if empty_keys:
            raise CheckError(f"These django settings should not be empty: {', '.join(empty_keys)}")

    def _check_database(self):
        from apigateway.core.models import Gateway

        try:
            Gateway.objects.exists()
        except Exception as err:
            raise CheckError(f"Query from database failed, error: {err}")

    def _check_redis(self):
        config = getattr(settings, "CHANNEL_REDIS_CONFIG", None)
        client = redis.Redis(connection_pool=get_redis_pool(config))
        try:
            client.ping()

            key = "apigateway_healthz_check"
            client.set(key, "apigateway")
            client.expire(key, 60)
            client.get(key)
        except Exception as err:
            raise CheckError(f"Redis check failed [{config['host']}:{config['port']}], error: {err}")

    def _check_elasticsearch(self):
        client_class = get_es_client_class()
        client = client_class(
            request_id="not-exist-request-id",
            time_range=1,
        )
        try:
            client.search_logs()
        except APIError as err:
            es_client_type = settings.ACCESS_LOG_CONFIG["es_client_type"]
            raise CheckWarning(
                "Query request api logs failed, please check the project log for more error details, "
                f"client_type: {es_client_type}, error: {err.code.message}"
            )

    def _check_external_dependency_url(self):
        url_keys = [
            "BK_COMPONENT_API_URL",
            "BK_PAAS3_API_URL",
        ]
        for key in url_keys:
            url = getattr(settings, key)
            try:
                resp = requests.get(url, timeout=3, verify=False)
            except RequestException as err:
                raise CheckError(f"Request api error, url: {url}, error: {err}")

            if resp.status_code >= 500:
                raise CheckError(
                    f"Request api status_code >= 500, url: {url}, "
                    f"status_code: {resp.status_code}, response content: {resp.text}"
                )

    def _check_bk_paasv3(self):
        url = settings.BK_PAAS3_API_URL.rstrip("/") + "/prod/system/uni_applications/query/by_id/"
        try:
            resp = requests.get(
                url,
                params={
                    "id": [settings.BK_APP_CODE],
                    "private_token": getattr(settings, "BK_PAAS3_PRIVATE_TOKEN", ""),
                    "format": "bk_std_json",
                },
                headers={
                    "x-bkapi-authorization": json.dumps(
                        {
                            "bk_app_code": settings.BK_APP_CODE,
                            "bk_app_secret": settings.BK_APP_SECRET,
                        }
                    )
                },
                timeout=3,
                verify=False,
            )
        except RequestException as err:
            raise CheckWarning(f"Request paas3.0 api to get application error, url: {url}, error: {err}")

        try:
            result = resp.json()
        except (TypeError, json.JSONDecodeError):
            raise CheckWarning(
                "The response to paas3.0 api is not a valid json, "
                "please check django settings: BK_APP_CODE, BK_APP_SECRET, "
                f"url: {url}, response content: {resp.text}, "
            )

        try:
            resp.raise_for_status()
        except HTTPError:
            raise CheckWarning(
                f"Request paas3.0 api to get application fail, request url: {url}, response: {resp.text}, "
                "please check django settings: BK_APP_CODE, BK_APP_SECRET"
            )
