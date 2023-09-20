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
import copy
import json

from common.constants import API_TYPE_Q
from components.component import Component
from esb.bkcore.models import ESBChannel
from esb.utils.esb_config import EsbConfigParser
from .toolkit import configs


class GetSynchronizedComponents(Component):
    """获取待同步的组件列表"""

    sys_name = configs.SYSTEM_NAME
    api_type = API_TYPE_Q

    def handle(self):
        # 获取 db 中的组件
        components = self._get_components_from_db()
        component_key_to_component = {
            self._get_component_key(component["method"], component["path"]): component for component in components
        }

        # 添加 rewrite 组件
        rewrite_channels = EsbConfigParser().get_rewrite_channels()
        for path, rewrite_path in rewrite_channels.items():
            rewrite_component_key = self._get_component_key(method="", path=rewrite_path)
            component = copy.deepcopy(component_key_to_component[rewrite_component_key])
            component.update(
                {
                    "id": None,
                    "path": path,
                    "name": f"{component['name']}_rewrite",
                    "is_public": False,
                }
            )
            component_key = self._get_component_key(method="", path=path)
            component_key_to_component[component_key] = component

        # 补全一些额外配置
        components = list(component_key_to_component.values())
        for component in components:
            component.update(
                {
                    "full_path": f"/api/c/compapi{component['path']}",
                    "verified_user_required": component["verified_user_required"],
                    "permission_level": component["permission_level"],
                }
            )

        self.response.payload = {
            "result": True,
            "data": components,
        }

    def _get_component_key(self, method: str, path: str) -> str:
        return f"{method}:{path}"

    def _get_components_from_db(self):
        components = ESBChannel.objects.values(
            "system__name",
            "id",
            "name",
            "description",
            "method",
            "path",
            "permission_level",
            "verified_user_required",
            "is_public",
            "config",
        )

        for component in components:
            component["system_name"] = component.pop("system__name")

            config = json.loads(component.pop("config"))
            component["suggest_method"] = config.get("suggest_method", "")

        return components
