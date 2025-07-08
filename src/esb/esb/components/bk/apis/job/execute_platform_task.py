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


class ExecutePlatformTask(Component):
    """
    apiLabel {{ _("启动平台作业") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("启动平台作业") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | task_id   |  int       | {{ _("是") }}     | {{ _("作业ID") }} |
    | source_app_id |  int   | {{ _("否") }}     | {{ _("源业务ID") }} |
    | target_app_id |  int   | {{ _("是") }}     | {{ _("目标业务ID") }} |
    | steps     |  array     | {{ _("否") }}     | {{ _("步骤参数") }} |

    #### steps

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | scriptTimeout |  int     | {{ _("否") }}     | {{ _("脚本超时时间") }} |
    | scriptParam   |  string  | {{ _("否") }}     | {{ _("脚本参数") }} |
    | scriptContent |  string  | {{ _("否") }}     | {{ _("执行脚本步骤的脚本内容，base64编码后的内容，与scriptId二选一，二者同时存在，以scriptId为准") }} |
    | scriptType    |  int     | {{ _("否") }}     | {{ _("执行脚本的类型，1.shell脚本、2.bat脚本、3.perl脚本、4.python脚本、5(Powershell脚本)；如果scriptContent存在，则必填") }} |
    | ipList        |  string  | {{ _("否") }}     | {{ _("IP列表格式，云区域ID:IP，多个之间逗号分割，例如1:1.0.0.1,1:1.0.0.2") }} |
    | scriptId      |  int     | {{ _("否") }}     | {{ _("脚本ID") }} |
    | stepId        |  int     | {{ _("否") }}     | {{ _("步骤ID，可以只指定某几步执行") }} |
    | account       |  string  | {{ _("否") }}     | {{ _("执行账户账户名") }} |
    | fileTargetPath |  string | {{ _("否") }}     | {{ _("目标路径") }} |
    | fileSource    |  array   | {{ _("否") }}     | {{ _("源文件信息，整个参数替换，不支持内部某个变量替换。格式参考下面说明") }} |

    #### fileSource

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | file      |  string    | {{ _("是") }}     | {{ _("文件路径，如：/tmp/t.txt") }} |
    | ipList    |  string    | {{ _("是") }}     | {{ _("源文件服务器地址，格式为：子网ID:IP，多个之间逗号分割") }} |
    | account   |  string    | {{ _("是") }}     | {{ _("源文件机器执行账户账户名") }} |

    ### {{ _("请求参数示例") }}

    ```python
    {
        "task_id": 1,
        "target_app_id": 1,
        "steps": [{
            "scriptTimeout": 1000,
            "scriptParam": "-a",
            "ipList": "1:1.0.0.1,1:1.0.0.2",
            "scriptId": 1,
            "stepId": 1,
            "account": "root",
        },
        {
            "fileTargetPath": "/tmp/[FILESRCIP]/",
            "fileSource": [{
                "file": "/tmp/t.txt",
                "ipList": "1:1.0.0.3,1:1.0.0.4",
                "account": "root",
            }],
            "ipList": "1:1.0.0.1,1:1.0.0.2",
            "stepId": 2,
            "account": "root",
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
            "taskInstanceId": 168231
        }
    }
    ```
    """  # noqa

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    class Form(BaseComponentForm):
        task_id = forms.CharField(label="task ID", required=True)
        source_app_id = forms.IntegerField(label="source business ID", required=False)
        target_app_id = forms.IntegerField(label="target business ID", required=True)
        steps = TypeCheckField(label="step parameters", promise_type=list, required=False)

        def clean(self):
            data = self.cleaned_data
            params = {
                "taskId": data["task_id"],
                "sourceAppId": data.get("source_app_id") or 0,
                "targetAppId": data["target_app_id"],
            }
            if data.get("steps"):
                params.update(steps=data["steps"])
            return params

    def handle(self):
        data = self.form_data
        data["starter"] = self.current_user.username

        client = tools.JOBClient(self.outgoing.http_client)
        params = tools.get_basic_json("executePlatformTask", params=data)
        result = client.post(self.host, data=params)

        self.response.payload = result
