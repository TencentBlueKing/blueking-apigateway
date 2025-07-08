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

import json

from common.constants import API_TYPE_OP
from components.component import ConfComponent
from .toolkit import configs


class JobComponent(ConfComponent):

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    def handle(self):
        request_info = self.get_request_info(
            extra_params={
                "bk_username": self.current_user.username,
                "bk_app_code": self.request.app_code,
            }
        )

        if self.dest_http_method == "GET":
            data = json.dumps(request_info["params"])
        else:
            data = request_info["data"]

        self.response.payload = self.outgoing.http_client.post(
            host=self.host,
            path=request_info["path"],
            data=data,
            verify=True,
            response_encoding="utf-8",
            with_jwt_header=True,
            cert=(configs.CLIENT_CERT, configs.CLIENT_KEY),
            headers={
                "Bk-Username": self.current_user.username,
                "Bk-App-Code": self.request.app_code,
                "X-Bkapi-Request-Id": self.request.request_id,
                "Blueking-Language": self.request.bk_language,
                "Content-Type": "application/json",
            },
        )
