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

from django import forms

from common.constants import API_TYPE_Q
from common.forms import BaseComponentForm
from components.component import Component
from .toolkit import configs


class GetUser(Component):
    """
    apiLabel {{ _("获取用户信息") }}
    apiMethod GET

    ### {{ _("功能描述") }}

    {{ _("获取用户信息") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    ### {{ _("请求参数示例") }}

    ```python
    {
        "app_code": "esb_test",
        "app_secret": "xxx",
        "bk_token": "xxx",
    }
    ```
    ### {{ _("返回结果示例") }}
    ```python
    {
        "result": true,
        "code": "00",
        "message": "OK",
        "data": {
            "username": "admin",
            "qq": "12345",
            "phone": "12345678911",
            "role": "1",
            "email": "11@qq.com",
            "chname": "admin"
        },
    }
    ```

    ### {{ _("返回结果参数说明") }}

    | {{ _("字段") }}      | {{ _("类型") }}      | {{ _("描述") }}      |
    |-----------|-----------|-----------|
    | data      | object    | {{ _("返回数据，成功返回请求数据") }} |

    #### data

    | {{ _("字段") }}      | {{ _("类型") }}      | {{ _("描述") }}      |
    |-----------|-----------|-----------|
    | role      | string    | {{ _("用户角色，0：普通用户，1：超级管理员，2：开发者，3：职能化用户，4：审计员") }} |
    """

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        bk_token = forms.CharField(label="login token", required=False)
        username = forms.CharField(label="username", required=False)
        bk_username = forms.CharField(label="bk_username", required=False)

        def clean(self):
            data = self.cleaned_data
            return {
                "bk_token": data["bk_token"],
                "username": data["username"] or data["bk_username"],
            }

    def handle(self):
        self.response.payload = self.outgoing.http_client.get(
            configs.host,
            "/login/accounts/get_user/",
            params=self.form_data,
            headers=configs.headers,
        )
