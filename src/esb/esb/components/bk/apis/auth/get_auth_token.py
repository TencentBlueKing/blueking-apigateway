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

import datetime

from django.utils import timezone

from common.base_utils import generate_token
from common.constants import API_TYPE_Q
from components.component import Component
from esb.bkcore.models import AccessToken
from .toolkit import configs


class GetAuthToken(Component):
    """
    apiLabel 获取AuthToken
    apiMethod GET

    ### 功能描述

    获取AuthToken

    ### 请求参数

    {{ common_args_desc }}

    ### 请求参数示例

    ```python
    {
        "app_code": "esb_test",
        "app_secret": "xxx",
        "bk_token": "xxx",
    }
    ```

    ### 返回结果示例

    ```python
    {
        "result": true,
        "code": "00",
        "message": "",
        "data": {
            "username": "alex",
            "auth_token": "1V8E8MMybNq5S8WDU4pO5hImxk5ldO",
            "expires_in": 15551578
        }
    }
    ```
    """

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    def _get_auth_token(self, app_code, username):
        return AccessToken.objects.filter(bk_app_code=app_code, user_id=username).first()

    def _create_auth_token(self, app_code, username):
        return AccessToken.objects.create(
            bk_app_code=app_code,
            user_id=username,
            access_token=generate_token(),
            expires=timezone.now() + datetime.timedelta(days=configs.ACCESS_TOKEN_EXPIRE_DAYS),
        )

    def handle(self):
        app_code = self.request.app_code
        username = self.current_user.username

        token = self._get_auth_token(app_code, username)
        if not token:
            token = self._create_auth_token(app_code=app_code, username=username)
        elif token.has_expired():
            # 判断如果token已经过期，生成一个新的token
            token.access_token = generate_token()
            token.expires = timezone.now() + datetime.timedelta(days=configs.ACCESS_TOKEN_EXPIRE_DAYS)
            token.save()

        self.response.payload = {
            "result": True,
            "data": {
                "auth_token": token.access_token,
                "username": token.user_id,
                "expires_in": token.expires_in(),
            },
        }
