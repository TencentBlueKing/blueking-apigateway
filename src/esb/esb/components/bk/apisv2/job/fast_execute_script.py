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

from common.constants import API_TYPE_OP, HTTP_METHOD
from common.forms import BaseComponentForm, TypeCheckField
from components.component import Component
from .toolkit import configs, tools


class FastExecuteScript(Component):
    suggest_method = HTTP_METHOD.POST
    label = u"快速执行脚本"
    label_en = "Fast execute script"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    class Form(BaseComponentForm):
        bk_biz_id = forms.IntegerField(label="business id", required=True)
        script_id = forms.IntegerField(label="script id", required=False)
        task_name = forms.CharField(label="task name", required=False)
        script_content = forms.CharField(label="script content", required=False)
        script_param = forms.CharField(label="script parameters", required=False)
        script_timeout = forms.IntegerField(label="script timeout", required=False)
        account = forms.CharField(label="account name", required=False)
        is_param_sensitive = forms.IntegerField(label="a sensitive parameter or not", required=False)
        script_type = forms.IntegerField(label="script type", required=False)
        ip_list = TypeCheckField(label="ip list", promise_type=list, required=False)
        custom_query_id = TypeCheckField(label="custom query id", promise_type=list, required=False)
        bk_callback_url = forms.CharField(label="callback url", required=False)

        def clean(self):
            data = self.cleaned_data
            param_keys = [
                "script_id",
                "task_name",
                "script_content",
                "script_param",
                "script_timeout",
                "account",
                "is_param_sensitive",
                "script_type",
                "ip_list",
                "custom_query_id",
            ]
            return {
                "bk_biz_id": data["bk_biz_id"],
                "params": self.get_cleaned_data_when_exist(param_keys),
                "bk_callback_url": data["bk_callback_url"],
            }

    def handle(self):
        params = tools.get_action_params(
            action="fast_execute_script",
            params=self.form_data,
            operator=self.current_user.username,
            app_code=self.request.app_code,
            request_id=self.request.request_id,
        )

        client = tools.JOBClient(self.outgoing.http_client)
        self.response.payload = client.post(
            self.host, "/api/v2/fast_execute_script", data=params, bk_language=self.request.bk_language
        )
