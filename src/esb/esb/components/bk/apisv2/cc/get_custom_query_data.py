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


class GetCustomQueryData(Component):
    suggest_method = HTTP_METHOD.GET
    label = u"根据自定义查询获取数据"
    label_en = "get customize query data"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    host = configs.host

    class Form(BaseComponentForm):
        bk_biz_id = forms.IntegerField(label="business id", required=True)
        id = forms.CharField(label="id", required=True)
        start = forms.IntegerField(label="start", required=True)
        limit = forms.IntegerField(label="limit", required=True)

    def handle(self):
        client = tools.CCClient(self)
        self.response.payload = client.get(
            host=self.host,
            path="/api/v3/userapi/data/{bk_biz_id}/{id}/{start}/{limit}".format(**self.form_data),
        )
