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

from common.constants import API_TYPE_Q, HTTP_METHOD
from common.forms import BaseComponentForm, ListField
from components.component import Component
from .toolkit import configs, tools


class GetBatchUsersPlatformRole(Component):
    suggest_method = HTTP_METHOD.POST
    label = u"批量获取用户各平台角色信息"
    label_en = "get role of the users in platforms"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        bk_username_list = ListField(label="username list", required=True)
        bk_token = forms.CharField(label="login token", required=False)

    def handle(self):
        client = tools.LOGINClient(self.outgoing.http_client)
        self.response.payload = client.post(
            host=configs.host,
            path="/login/api/v2/get_batch_users_platform_role/",
            data=json.dumps(self.form_data),
        )
