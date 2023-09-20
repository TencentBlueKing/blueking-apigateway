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

from django import forms
from django.utils import translation

from common.base_utils import html_escape
from common.constants import API_TYPE_Q
from common.forms import BaseComponentForm
from components.component import Component
from esb.bkcore.constants import LegacyPermissionLevel
from esb.bkcore.models import AppComponentPermission, ESBChannel, System
from .toolkit import configs


class GetComponents(Component):
    """"""

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    class Form(BaseComponentForm):
        system_name = forms.CharField(label="system name", required=True)
        searched_app_code = forms.CharField(label="app_code", required=False)

    def handle(self):
        data = self.form_data
        try:
            system = System.objects.get(name=data["system_name"])
        except System.DoesNotExist:
            self.response.payload = {"result": False, "message": "system [%s] does not exist" % data["system_name"]}
            return

        channels = ESBChannel.objects.filter(system_id=system.id, is_public=True)
        components = []
        searched_app_code = data["searched_app_code"]

        bk_language = self.request.headers.get("Blueking-Language", "en")
        with translation.override(bk_language):
            for channel in channels:
                legacy_permission_level = LegacyPermissionLevel.from_new(channel.permission_level)

                components.append(
                    {
                        "id": channel.id,
                        "name": html_escape(channel.name),
                        "label": html_escape(channel.description_display),
                        "perm_level": legacy_permission_level.value,
                        "perm_level_label": legacy_permission_level.label,
                        "app_has_component_perm": self._has_component_permission(channel, searched_app_code),
                    }
                )

        self.response.payload = {"result": True, "data": components}

    def _has_component_permission(self, channel, bk_app_code):
        if not channel.component_permission_required:
            return True

        if bk_app_code:
            return AppComponentPermission.objects.has_permission(bk_app_code, channel.id)

        return False
