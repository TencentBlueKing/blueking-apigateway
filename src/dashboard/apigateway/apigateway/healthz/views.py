#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from django.conf import settings
from django.http import HttpResponse
from django.views.generic import View

from apigateway.utils.redis_utils import new_redis_client
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
        ]
        empty_keys = [key for key in not_allow_empty_keys if not getattr(settings, key, None)]
        if empty_keys:
            raise CheckError("check settings failed")

    def _check_database(self):
        from apigateway.core.models import Gateway  # noqa

        try:
            Gateway.objects.exists()
        except Exception:  # pylint: disable=broad-except
            logger.exception("healthz database check failed")
            raise CheckError("check database failed")

    def _check_redis(self):
        config = getattr(settings, "CHANNEL_REDIS_CONFIG", None)
        client = None
        try:
            client = new_redis_client(config)
            client.ping()

            key = "apigateway_healthz_check"
            client.set(key, "apigateway")
            client.expire(key, 60)
            client.get(key)
        except Exception:  # pylint: disable=broad-except
            logger.exception("healthz redis check failed")
            raise CheckError("check redis failed")
        finally:
            # 每次检查都会新建连接，检查完成后关闭，避免连接泄漏
            if client is not None:
                client.close()
