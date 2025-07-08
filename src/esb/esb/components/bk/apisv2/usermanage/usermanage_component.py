# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

from django.conf import settings

from common.constants import API_TYPE_Q
from components.component import ConfComponent
from .toolkit import configs


class UsermanageComponent(ConfComponent):

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    def handle(self):
        extra_params = {}
        username = self.request.kwargs.get("username")
        if username:
            extra_params["username"] = username

        request_info = self.get_request_info(extra_params=extra_params)

        # bk-user 要求 app_code 不能为空，而 cmsi tools 调用此组件时，未传递 app_code,
        # 为更好地兼容 cmsi 作为自定义组件的场景，值为空时替换为网关的 app_code
        if not self.request.app_code:
            self.request.app_code = getattr(settings, "BK_APP_CODE", "")

        response = self.outgoing.http_client.request(
            self.dest_http_method,
            host=configs.host,
            path=request_info["path"],
            params=request_info["params"],
            data=request_info["data"],
            response_encoding="utf-8",
            with_jwt_header=True,
            headers={
                "Bk-Username": self.current_user.username,
                "Bk-App-Code": self.request.app_code,
                "Content-Type": "application/json",
            },
        )

        self.response.payload = response
