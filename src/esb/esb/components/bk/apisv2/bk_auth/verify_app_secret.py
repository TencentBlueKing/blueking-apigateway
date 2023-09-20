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
import json

from django import forms

from common.constants import API_TYPE_OP, HTTP_METHOD
from common.forms import BaseComponentForm
from components.component import Component
from .toolkit import configs


class VerifyAppSecret(Component):
    suggest_method = HTTP_METHOD.POST
    label = u"验证 AppSecret"
    label_en = "verify app secret"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    class Form(BaseComponentForm):
        target_app_code = forms.CharField(label="app code", required=True)
        target_app_secret = forms.CharField(label="app secret", required=True)

    def handle(self):
        result = self.outgoing.http_client.post(
            host=configs.host,
            path="/api/v1/apps/{bk_app_code}/access-keys/verify".format(bk_app_code=self.form_data["target_app_code"]),
            data=json.dumps({"bk_app_secret": self.form_data["target_app_secret"]}),
            headers=self._prepare_headers(),
            response_encoding="utf-8",
            allow_non_200=True,
        )

        result["result"] = result["code"] == 0

        self.response.payload = result

    def _prepare_headers(self):
        headers = {"Content-Type": "application/json"}
        headers.update(configs.headers)
        return headers
