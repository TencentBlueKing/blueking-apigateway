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
from common.forms import BaseComponentForm, TypeCheckField
from components.component import Component
from .toolkit import configs, tools


class CreateModule(Component):
    suggest_method = HTTP_METHOD.POST
    label = u"创建模块"
    label_en = "create module"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_OP

    host = configs.host

    class Form(BaseComponentForm):
        bk_supplier_account = forms.CharField(label="bk supplier account", required=False)
        bk_biz_id = forms.IntegerField(label="business id", required=True)
        bk_set_id = forms.IntegerField(label="set id", required=True)
        data = TypeCheckField(label="data", promise_type=dict, required=True)

        def clean(self):
            data = self.get_cleaned_data_when_exist()
            data.setdefault("bk_supplier_account", configs.DEFAULT_BK_SUPPLIER_ACCOUNT)
            data["data"]["bk_supplier_account"] = data["bk_supplier_account"]
            return data

    def handle(self):
        client = tools.CCClient(self)
        self.response.payload = client.post(
            host=self.host,
            path="/api/v3/module/{bk_biz_id}/{bk_set_id}".format(**self.form_data),
            data=json.dumps(self.form_data["data"]),
        )
