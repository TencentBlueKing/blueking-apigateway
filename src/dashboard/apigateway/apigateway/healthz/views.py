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

import redis
import requests
from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View
from requests.exceptions import HTTPError, RequestException

from apigateway.utils.redis_utils import get_redis_pool
from apigateway.utils.responses import FailJsonResponse, OKJsonResponse

logger = logging.getLogger(__name__)


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
        ]

        for checker in checkers:
            try:
                checker()
            except CheckError as err:
                return FailJsonResponse(status=500, code="UNKNOWN", message=str(err))
            except CheckWarning as err:
                return OKJsonResponse(data={"message": f"Warning: {err}"})

        return OKJsonResponse()

    def _check_settings(self):
        """检查 django settings 配置"""
        not_allow_empty_keys = [
            # "ENCRYPT_KEY",
            "SECRET_KEY",
            "BK_APP_CODE",
            "BK_APP_SECRET",
            "BK_PAAS3_API_URL",
            "BK_COMPONENT_API_URL",
        ]
        empty_keys = [key for key in not_allow_empty_keys if not getattr(settings, key, None)]
        if empty_keys:
            raise CheckError("check settings failed")

    def _check_database(self):
        from apigateway.core.models import Gateway

        try:
            Gateway.objects.exists()
        except Exception as err:
            logger.exception("healthz database check failed")
            raise CheckError("check database failed")

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
            logger.exception("healthz redis check failed")
            raise CheckError("check redis failed")

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
                logger.exception("healthz external dependency url check failed")
                raise CheckError("check external dependency url failed")

            if resp.status_code >= 500:
                raise CheckError("check external dependency url failed")

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
            logger.exception("healthz bk_paasv3 check failed")
            raise CheckWarning("check bk_paasv3 failed")

        try:
            result = resp.json()
        except (TypeError, json.JSONDecodeError):
            logger.exception("healthz bk_paasv3 check failed")
            raise CheckWarning("check bk_paasv3 failed")

        try:
            resp.raise_for_status()
        except HTTPError as err:
            logger.exception("healthz bk_paasv3 check failed")
            raise CheckWarning("check bk_paasv3 failed")
