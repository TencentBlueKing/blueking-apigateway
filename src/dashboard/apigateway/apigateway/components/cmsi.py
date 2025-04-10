# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from bkapi_client_core.esb import Operation
from bkapi_client_core.exceptions import BKAPIError
from bkapi_component.open.shortcuts import get_client_by_username
from django.conf import settings
from django.utils.translation import gettext as _

from apigateway.utils.url import url_join

from .http import http_post
from .utils import do_blueking_http_request, gen_gateway_headers

logger = logging.getLogger(__name__)


class BaseCMSIComponent(ABC):
    @abstractmethod
    def send_mail(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def send_wechat(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def send_im(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError


class CMSIComponent(BaseCMSIComponent):
    def _call_api(self, action: str, data: dict, username: str) -> Tuple[bool, str]:
        client = get_client_by_username(username)
        try:
            getattr(client.cmsi, action)(data)
        except BKAPIError as err:
            return False, _("发送消息失败，{err}").format(err=err)
        return True, ""

    def send_mail(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        return self._call_api("send_mail", params, username)

    def send_wechat(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        return self._call_api("send_weixin", params, username)

    def send_im(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        client = get_client_by_username(username)
        client.cmsi.register("send_rtx", Operation(method="POST", path="/api/c/compapi/v2/cmsi/send_rtx/"))
        try:
            client.cmsi.send_rtx(params)
        except BKAPIError as err:
            return False, _("发送消息失败，{err}").format(err=err)
        return True, ""


class BKCMSIGateway(BaseCMSIComponent):
    """
    send message with bk-cmsi, the protocol is almost same as esb cmsi(but still different)
    """

    def _call_bkcmsi_api(self, tenant_id: str, http_func, path, data, more_headers=None, timeout=30) -> Dict | List:
        # 默认请求头
        headers = gen_gateway_headers()
        if more_headers:
            headers.update(more_headers)

        headers["X-Bk-Tenant-Id"] = tenant_id

        host = settings.BK_API_URL_TMPL.format(api_name="bk-cmsi")

        url = url_join(host, path)

        return do_blueking_http_request("bk-cmsi", http_func, url, data, headers, timeout)

    def send_mail(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        if "receiver__username" in params and isinstance(params["receiver__username"], str):
            params["receiver__username"] = params["receiver__username"].split(";")

        url_path = "/prod/v1/send_mail/"
        try:
            self._call_bkcmsi_api(tenant_id, http_post, url_path, params)
        except Exception as err:
            logger.exception("send mail failed, tenant_id: %s, params: %s, username: %s", tenant_id, params, username)
            return False, _("发送消息失败，{err}").format(err=err)
        return True, ""

    def send_wechat(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        if "data" in params:
            message_data = params.pop("data")
            params["message_data"] = message_data

        url_path = "/prod/v1/send_weixin/"
        try:
            self._call_bkcmsi_api(tenant_id, http_post, url_path, params)
        except Exception as err:
            logger.exception(
                "send wechat failed, tenant_id: %s, params: %s, username: %s", tenant_id, params, username
            )
            return False, _("发送消息失败，{err}").format(err=err)
        return True, ""

    def send_im(self, tenant_id: str, params: dict, username: str = "") -> Tuple[bool, str]:
        # NOTE: only works in ieod-clouds, there is no im service in other clouds
        raise NotImplementedError


cmsi_component: BaseCMSIComponent

if settings.ENABLE_MULTI_TENANT_MODE:
    # FIXME: 应该也支持某些环境启动网关模式
    print("multi-tenant mode enabled, use bkcmsi gateway instead of cmsi component in esb")
    cmsi_component = BKCMSIGateway()
else:
    # NOTE: ieod-clouds should use this component, not the bk-cmsi-gateway
    cmsi_component = CMSIComponent()
