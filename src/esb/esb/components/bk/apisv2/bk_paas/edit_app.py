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

import json

from django import forms

from common.constants import API_TYPE_OP, HTTP_METHOD
from common.forms import BaseComponentForm, ListField
from components.component import Component
from .toolkit import configs, tools


class EditApp(Component):
    suggest_method = HTTP_METHOD.POST
    label = u"编辑轻应用"
    label_en = "edit application"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    class Form(BaseComponentForm):
        bk_light_app_code = forms.CharField(label="bk light app code", required=True)
        bk_light_app_name = forms.CharField(label="bk light app name", required=False)
        app_url = forms.CharField(label="app url", required=False)
        developer = ListField(label="developer", required=False)
        app_tag = forms.CharField(label="app tag", required=False)
        introduction = forms.CharField(label="introduction", required=False)
        width = forms.IntegerField(label="width", required=False)
        height = forms.IntegerField(label="height", required=False)

        def clean(self):
            param_keys = [
                "bk_light_app_code",
                "bk_light_app_name",
                "app_url",
                "developer",
                "app_tag",
                "introduction",
                "width",
                "height",
            ]
            params = self.get_cleaned_data_when_exist(param_keys)
            if "developer" in params:
                params["developer"] = ";".join(params["developer"])
            return params

    def handle(self):
        self.form_data["operator"] = self.current_user.username

        client = tools.PAASClient(self.outgoing.http_client)
        self.response.payload = client.post(
            host=self.host, path="/paas/api/v2/edit_app/", data=json.dumps(self.form_data)
        )
