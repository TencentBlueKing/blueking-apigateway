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

from common.constants import API_TYPE_Q, HTTP_METHOD
from components.component import Component
from esb.utils.jwt_utils import JWTKey
from .toolkit import configs


class GetApiPublicKey(Component):
    suggest_method = HTTP_METHOD.GET
    label = u"获取公钥"
    label_en = "Get api public key"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    def handle(self):
        public_key = JWTKey().get_public_key()

        self.response.payload = {
            "result": True if public_key else False,
            "data": {
                "public_key": public_key,
            },
        }
