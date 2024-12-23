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
from abc import ABC, abstractmethod
from typing import Tuple

from bkapi_client_core.esb import Operation
from bkapi_client_core.exceptions import BKAPIError
from bkapi_component.open.shortcuts import get_client_by_username
from django.conf import settings
from django.utils.translation import gettext as _


class BaseCMSIComponent(ABC):
    @abstractmethod
    def send_mail(self, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def send_wechat(self, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError

    @abstractmethod
    def send_im(self, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError


class CMSIComponent(BaseCMSIComponent):
    def _call_api(self, action: str, data: dict, username: str) -> Tuple[bool, str]:
        client = get_client_by_username(username)
        try:
            getattr(client.cmsi, action)(data)
        except BKAPIError as err:
            return False, _("发送消息失败，{err}").format(err=err)
        return True, ""

    def send_mail(self, params: dict, username: str = "") -> Tuple[bool, str]:
        return self._call_api("send_mail", params, username)

    def send_wechat(self, params: dict, username: str = "") -> Tuple[bool, str]:
        return self._call_api("send_weixin", params, username)

    def send_im(self, params: dict, username: str = "") -> Tuple[bool, str]:
        client = get_client_by_username(username)
        client.cmsi.register("send_rtx", Operation(method="POST", path="/api/c/compapi/v2/cmsi/send_rtx/"))
        try:
            client.cmsi.send_rtx(params)
        except BKAPIError as err:
            return False, _("发送消息失败，{err}").format(err=err)
        return True, ""


class BKCMSIGateway(BaseCMSIComponent):
    # FIXME: 如果新版本的 bk-cmsi 协议跟 esb cmsi 协议不一样，那么上层代码也需要修改
    # FIXME: 需要 ineject x-bk-tenant-id=> 需要获取对应网关的 tenant_id，发送时放入 header 头，以使用其渠道
    def send_mail(self, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError

    def send_wechat(self, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError

    def send_im(self, params: dict, username: str = "") -> Tuple[bool, str]:
        raise NotImplementedError


cmsi_component: BaseCMSIComponent

if settings.ENABLE_MULTI_TENANT_MODE:
    print("multi-tenant mode enabled, use bkcmsi gateway instead of cmsi component in esb")
    cmsi_component = BKCMSIGateway()
else:
    cmsi_component = CMSIComponent()
