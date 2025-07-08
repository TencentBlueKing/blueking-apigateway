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
from common.forms import BaseComponentForm, TypeCheckField
from components.component import Component
from .toolkit import configs, tools


class GetAgentStatus(Component):
    """
    apiLabel {{ _("查询Agent状态") }}
    apiMethod POST

    ### {{ _("功能描述") }}

    {{ _("查询Agent状态") }}

    ### {{ _("请求参数") }}

    {{ common_args_desc }}

    #### {{ _("接口参数") }}

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | app_id    |  int       | {{ _("是") }}     | {{ _("业务ID") }} |
    | ip_infos  |  array     | {{ _("是") }}     | {{ _("IP信息，每项条目包含信息见下面参数描述") }} |

    #### ip_infos

    | {{ _("字段") }}      |  {{ _("类型") }}      | {{ _("必选") }}   |  {{ _("描述") }}      |
    |-----------|------------|--------|------------|
    | ip        |  string    | {{ _("是") }}     | {{ _("IP地址") }} |
    | plat_id   |  int       | {{ _("是") }}     | {{ _("子网ID") }} |

    ### {{ _("请求参数示例") }}

    ```python
    {
        "app_code": "esb_test",
        "app_secret": "xxx",
        "bk_token": "xxx",
        "app_id": 1,
        "ip_infos": [
            {
                "ip": "1.0.0.1",
                "plat_id": 1,
            }
        ]
    }
    ```

    ### {{ _("返回结果示例") }}

    ```python
    {
        "result": true,
        "code": "00",
        "message": "",
        "data": [
            {
                "status": 1,
                "ip": "1.0.0.1"
            }
        ]
    }
    ```

    #### data

    | {{ _("字段") }}      | {{ _("类型") }}      | {{ _("描述") }}      |
    |-----------|-----------|-----------|
    | status    | int       | {{ _("主机Agent状态，1.正常; 0.异常") }} |
    """

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    host = configs.host

    class Form(BaseComponentForm):
        app_id = forms.IntegerField(label="business ID", required=True)
        ip_infos = TypeCheckField(label="ip information", promise_type=list, required=True)

        def clean(self):
            data = self.cleaned_data
            ip_infos = [GetAgentStatus.IPInfoForm(host).get_cleaned_data_or_error() for host in data["ip_infos"]]
            return {
                "ip_infos": ip_infos,
            }

    class IPInfoForm(BaseComponentForm):
        ip = forms.CharField(label="IP", required=True)
        plat_id = forms.IntegerField(label="subnet ID", required=True)

    def handle(self):
        data = self.form_data

        client = tools.JOBClient(self.outgoing.http_client)
        data = tools.get_basic_json(action="getAgentStatus", params=data)
        result = client.post(self.host, data=data)

        self.response.payload = result
