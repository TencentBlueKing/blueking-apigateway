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
from components.component import Component, SetupConfMixin
from .toolkit import configs, tools


class GetUser(Component, SetupConfMixin):
    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        corpid = forms.CharField(label="corp ID", required=True)
        corpsecret = forms.CharField(label="corp secret", required=True)
        userid = forms.CharField(label="userid", required=True)

    def get_wx_access_token(self, params):
        wx_token = self.invoke_other("generic.weixin_qy.get_token", kwargs=params)
        return wx_token["data"]["access_token"]

    def handle(self):
        client = tools.WEIXINClient(self.outgoing.http_client)
        access_token = self.get_wx_access_token(self.form_data)
        result = client.get(
            path="/cgi-bin/user/get", params={"access_token": access_token, "userid": self.form_data["userid"]}
        )
        self.response.payload = result
