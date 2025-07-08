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

from builtins import str

from common.constants import API_TYPE_Q
from common.forms import BaseComponentForm, ListField
from components.component import Component
from .toolkit import configs, tools


class GetBatchUser(Component):
    """
    apiLabel {{ _("获取多个用户信息") }}
    apiMethod GET

    ### {{ _("功能描述") }}

    {{ _("获取多个用户信息") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}  |  {{ _("类型") }} | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | username_list |  string    | {{ _("是") }}     | {{ _("待获取信息的用户名列表") }}  |

    ### {{ _("请求参数示例") }}

    ```python
    {
        "app_code": "esb_test",
        "app_secret": "xxx",
        "bk_token": "xxx",
        "username_list": "admin;test"
    }
    ```

    ### {{ _("返回结果示例") }}

    ```python
    {
        "result": true,
        "code": "00",
        "message": "OK",
        "data": {
            "admin": {
                "username": "admin",
                "qq": "123123",
                "phone": "11111111111",
                "role": "1",
                "email": "11@qq.com",
                "chname": "admin"
            }
        }
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
        username_list = ListField(label="username list", required=True)

        def clean(self):
            return self.get_cleaned_data_when_exist(keys={"username_list": "bk_username_list"})

    def handle(self):
        result = self.invoke_other("generic.v2.usermanage.get_batch_users", kwargs=self.form_data)
        result["code"] = "00" if result["code"] == 0 else str(result["code"])
        for username, user in list((result["data"] or {}).items()):
            result["data"][username] = tools.convert_user_info(user)
        self.response.payload = result
