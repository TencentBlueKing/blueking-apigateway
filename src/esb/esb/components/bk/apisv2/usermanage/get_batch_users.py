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

from common.constants import API_TYPE_Q
from common.forms import BaseComponentForm, ListField
from components.component import Component
from .toolkit import configs


class GetBatchUsers(Component):
    """
    apiLabel 获取多个用户信息
    apiMethod POST
    """

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        bk_username_list = ListField(label="username list", required=True)

    def handle(self):
        params = {
            "lookup_field": "username",
            "no_page": True,
            "best_match": 1,
            "exact_lookups": ",".join(self.form_data["bk_username_list"]),
            "fields": "username,country_code,telephone,email,wx_userid,display_name,qq,language,time_zone",
        }

        result = self.invoke_other("generic.v2.usermanage.list_users", kwargs=params)
        if result["result"]:
            result["data"] = dict([(user["username"], user) for user in result["data"]])
        self.response.payload = result
