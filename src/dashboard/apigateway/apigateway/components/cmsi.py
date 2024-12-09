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
from typing import Tuple

from bkapi_client_core.esb import Operation
from bkapi_client_core.exceptions import BKAPIError
from bkapi_component.open.shortcuts import get_client_by_username
from django.utils.translation import gettext as _

# FIXME: upgrade to new cmsi gateway
# FIXME: 需要 ineject x-bk-tenant-id=> 需要获取对应网关的 tenant_id，发送时放入 header 头，以使用其渠道

# FIXME: remove bkapi_client_core from pyproject.toml


# FIXME: 内部上云版怎么办，还得继续使用 bk-esb 的 cmsi 组件


class CMSIComponent:
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


cmsi_component = CMSIComponent()
