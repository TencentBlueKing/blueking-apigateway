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

from common.base_utils import str_bool
from common.constants import API_TYPE_Q, HTTP_METHOD
from components.component import Component, SetupConfMixin
from .toolkit import configs


class GetMsgType(Component, SetupConfMixin):
    suggest_method = HTTP_METHOD.GET
    label = u"查询消息发送类型"
    label_en = "Get message type"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    def handle(self):
        bk_language = self.request.headers.get("Blueking-Language", "en")

        msg_type = []
        for mt in configs.msg_type:
            is_active = mt.get("is_active", str_bool(getattr(self, mt["type"], False)))
            msg_type.append(
                {
                    "type": mt["type"],
                    "icon": mt["active_icon"] if is_active else mt["unactive_icon"],
                    "label": mt["label_en"] if bk_language == "en" else mt["label"],
                    "is_active": is_active,
                }
            )

        self.response.payload = {
            "result": True,
            "data": msg_type,
        }
