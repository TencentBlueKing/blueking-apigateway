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

from common.constants import API_TYPE_OP
from common.forms import BaseComponentForm, TypeCheckField
from components.component import Component
from .toolkit import configs, tools


class ExecuteTaskExt(Component):
    """
    apiLabel {{ _("启动作业Ext(带全局变量启动)") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("启动作业Ext(带全局变量启动)") }}

    {{ _("如果全局变量的类型为IP，参数值必须包含groupIds或ipList。没有设置的参数将使用作业模版中的默认值") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | app_id    |  int       | {{ _("是") }}     | {{ _("业务ID") }} |
    | task_id   |  int       | {{ _("是") }}     | {{ _("作业ID") }} |
    | global_var|  array     | {{ _("是") }}     | {{ _("全局变量信息，作业包含的全局变量和类型可以通过接口“查询作业模板详情”(get_task_detail)获取") }} |

    ### {{ _("请求参数示例") }}

    ```python
    {
        "app_code": "esb_test",
        "app_secret": "xxx",
        "bk_token": "xxx",
        "app_id": "1",
        "task_id": "195",
        "global_var": [{
            "id": 436,
            "ipList": "1:1.0.0.1",
        },
        {
            "id": 437,
            "value": "newValue",
        }]
    }
    ```

    ### {{ _("返回结果示例") }}

    ```python
    {
        "result": true,
        "code": "00",
        "message": "",
        "data": {
            "taskInstanceName": "Test",
            "taskInstanceId": 10000
        }
    }
    ```
    """

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    class Form(BaseComponentForm):
        app_id = forms.CharField(label="business ID", required=True)
        task_id = forms.CharField(label="task ID", required=True)
        global_var = TypeCheckField(label="global variables", promise_type=list, required=False)

        def clean(self):
            data = self.cleaned_data
            result = {
                "taskId": data["task_id"],
            }
            if data.get("global_var"):
                result.update(globalVar=data["global_var"])
            return result

    def handle(self):
        data = self.form_data
        data["starter"] = self.current_user.username

        client = tools.JOBClient(self.outgoing.http_client)
        params = tools.get_basic_json("executeTaskExt", params=data)
        result = client.post(self.host, data=params)

        self.response.payload = result
