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

from common.constants import API_TYPE_Q, HTTP_METHOD
from common.forms import BaseComponentForm
from components.component import Component
from .toolkit import configs, tools


class GetJobInstanceGlobalVarValue(Component):
    suggest_method = HTTP_METHOD.GET
    label = u"获取作业实例全局变量的值"
    label_en = "Get job instance global variable value"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    host = configs.host

    class Form(BaseComponentForm):
        bk_biz_id = forms.IntegerField(label="business id", required=True)
        job_instance_id = forms.CharField(label="job instance id", required=True)

        def clean(self):
            data = self.cleaned_data
            return {"bk_biz_id": data["bk_biz_id"], "params": {"job_instance_id": data["job_instance_id"]}}

    def handle(self):
        params = tools.get_action_params(
            action="get_job_instance_global_var_value",
            params=self.form_data,
            operator=self.current_user.username,
            app_code=self.request.app_code,
            request_id=self.request.request_id,
        )

        client = tools.JOBClient(self.outgoing.http_client)
        self.response.payload = client.post(
            self.host, "/api/v2/get_job_instance_global_var_value", data=params, bk_language=self.request.bk_language
        )
