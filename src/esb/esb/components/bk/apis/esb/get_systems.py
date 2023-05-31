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
from common.constants import API_TYPE_Q
from components.component import Component
from esb.bkcore.models import ESBChannel, System

from .toolkit import configs


class GetSystems(Component):
    """"""

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    def handle(self):
        queryset = System.objects.all()
        systems = []

        bk_language = self.request.headers.get("Blueking-Language", "en")
        with translation.override(bk_language):
            for system in queryset:
                if not ESBChannel.objects.filter(system_id=system.id, is_public=True).exists():
                    continue

                systems.append(
                    {
                        "name": html_escape(system.name),
                        "label": html_escape(system.description_display),
                    }
                )

        self.response.payload = {"result": True, "data": systems}
