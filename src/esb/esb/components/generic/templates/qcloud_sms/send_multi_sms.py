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
from common.forms import BaseComponentForm, ListField
from components.component import Component, SetupConfMixin
from .toolkit import configs, tools


class SendMultiSms(Component, SetupConfMixin):
    """"""

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    class Form(BaseComponentForm):
        sdk_app_id = forms.CharField(label="tencent cloud sdkappid", required=True)
        app_key = forms.CharField(label="tencent cloud appkey", required=True)
        sms_type = forms.IntegerField(label="sms type", required=False)
        tel = ListField(label="tel", required=True)
        content = forms.CharField(label="content", required=True)
        extend = forms.CharField(label="extend", required=False)
        ext = forms.CharField(label="ext", required=False)
        sms_sign = forms.CharField(label="sign", required=False)

        def clean(self):
            data = self.cleaned_data

            # 为content添加短信签名
            sms_sign = data.get("sms_sign")
            content = data["content"]
            if sms_sign and not content.startswith(u"【"):
                sms_sign = sms_sign if sms_sign.startswith(u"【") else u"【%s】" % sms_sign
                content = sms_sign + content

            return {
                "tel": [
                    {
                        "nationcode": item.get("nation_code") or configs.default_nation_code,
                        "mobile": item["telephone"],
                    }
                    for item in data["tel"]
                ],
                "type": data["sms_type"] or 0,
                "msg": content,
                "extend": data["extend"],
                "ext": data["ext"],
            }

    def handle(self):
        sdk_app_id = self.request.kwargs.get("sdk_app_id")
        app_key = self.request.kwargs.get("app_key")

        client = tools.QCloudSmsClient(self.outgoing.http_client)
        rnd = client.get_random()
        cur_time = client.get_cur_time()
        self.form_data["time"] = cur_time
        self.form_data["sig"] = client.calculate_sig(
            app_key, rnd, cur_time, [item["mobile"] for item in self.form_data["tel"]]
        )

        result = client.post(
            "/v5/tlssmssvr/sendmultisms2?sdkappid=%s&random=%s" % (sdk_app_id, rnd),
            data=self.form_data,
        )
        self.response.payload = result
