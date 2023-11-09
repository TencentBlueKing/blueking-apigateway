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

from django.utils.translation import gettext as _

logger = logging.getLogger(__name__)


class BaseComponent:
    HOST = ""

    def _call_api(self, http_func, path, data, **kwargs):
        if not self.HOST:
            return False, _("未配置接口地址。"), None

        url = self._urljoin(self.HOST, path)
        http_ok, resp = http_func(url, data, **kwargs)

        ok, message, data = self.parse_response(http_ok, resp)

        if not ok:
            logger.error(
                "request third-party api failed. method=%s, url=%s, data=%s, response=%s",
                http_func.__name__,
                url,
                data,
                resp,
            )

        return ok, message, data

    def parse_response(self, http_ok, resp):
        ok = bool(http_ok and resp and resp.get("result"))
        message = ""
        data = None
        if http_ok and resp:
            message = resp.get("message", "")
            data = resp.get("data", None)
        return ok, message, data

    def _urljoin(self, host: str, path: str) -> str:
        if path.startswith("/"):
            host = host.rstrip("/")
        return f"{host}{path}"
