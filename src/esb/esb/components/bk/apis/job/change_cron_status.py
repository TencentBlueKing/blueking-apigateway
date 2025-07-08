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
from common.forms import BaseComponentForm
from components.component import Component
from .toolkit import configs, tools


class ChangeCronStatus(Component):
    """
    apiLabel {{ _("更新定时作业状态") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("更新定时作业状态，如启动或暂停；操作者必须是业务的创建人或运维") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | app_id |  int    | {{ _("是") }}     | {{ _("业务ID") }} |
    | status |  string    | {{ _("是") }}     | {{ _("作业状态，1.启动、2.暂停") }} |
    | crontab_task_id |  int    | {{ _("是") }}     | {{ _("定时任务ID") }} |

    ### {{ _("请求参数示例") }}

    ```python
    {
        "app_code": "esb_test",
        "app_secret": "xxx",
        "bk_token": "xxx",
        "app_id": 46,
        "status": "1",
        "crontab_task_id": 123,
    }
    ```

    ### {{ _("返回结果示例") }}

    ```python
    {
        "result": true,
        "code": "00",
        "message": "",
        "data": {
            "crontabTaskId": 2
        }
    }
    ```
    """

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    class Form(BaseComponentForm):
        app_id = forms.IntegerField(label="business ID", required=True)
        status = forms.CharField(label="job status", required=True)
        crontab_task_id = forms.IntegerField(label="cron task ID", required=True)

        def clean(self):
            data = self.cleaned_data
            params = {
                "appId": data["app_id"],
                "status": data["status"],
                "crontabTaskId": data["crontab_task_id"],
            }
            return params

    def handle(self):
        data = self.form_data
        data["operator"] = self.current_user.username

        client = tools.JOBClient(self.outgoing.http_client)
        data = tools.get_basic_json(action="changCronStatus", params=data)
        result = client.post(self.host, data=data)

        self.response.payload = result
