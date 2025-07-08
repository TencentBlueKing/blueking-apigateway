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

from common.constants import API_TYPE_OP
from common.errors import error_codes
from components.component import ConfComponent
from .toolkit import configs, tools


class CcComponent(ConfComponent):

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    def handle(self):
        self.request.kwargs.setdefault("bk_supplier_account", configs.DEFAULT_BK_SUPPLIER_ACCOUNT)

        request_info = self.get_request_info()

        client = tools.CCClient(self)
        request_handler = getattr(client, self.dest_http_method.lower(), None)
        if not request_handler:
            raise error_codes.REQUEST_DEST_METHOD_ERROR.format_prompt(self.dest_http_method.upper())
        self.response.payload = request_handler(
            host=self.host,
            path=request_info["path"],
            params=request_info["params"],
            data=request_info["data"],
        )
