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

from django.utils import translation

from common.base_utils import html_escape
from common.constants import API_TYPE_Q, HTTP_METHOD
from common.forms import BaseComponentForm, ListField
from components.component import Component
from esb.bkcore.models import ESBChannel

from .toolkit import configs


class GetComponents(Component):
    suggest_method = HTTP_METHOD.POST
    label = "获取指定系统的组件列表"
    label_en = "Get components"

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        system_names = ListField(label="system name", required=True)

    def handle(self):
        queryset = ESBChannel.objects.filter(
            system__name__in=self.form_data["system_names"],
            is_public=True,
        )

        component_list = []
        bk_language = self.request.headers.get("Blueking-Language", "en")
        with translation.override(bk_language):
            for channel in queryset:
                component_list.append(
                    {
                        "name": channel.name,
                        "label": html_escape(channel.description_display),
                        "method": channel.method or channel.config.get("suggest_method", ""),
                        "path": channel.api_path,
                        "system_id": channel.system_id,
                        "system_name": channel.system.name,
                        "version": channel.api_version,
                        "category": "component",
                        # 类型：执行类、查询类，填写固定值，保留协议兼容
                        "type": 1,
                    }
                )

        self.response.payload = {
            "result": True,
            "data": component_list,
        }
