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
from typing import Any, Dict, List

from attrs import define

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.core.models import Gateway


@define
class PluginBindingValidator:
    gateway: Gateway
    scope_type: PluginBindingScopeEnum
    scope_ids: List[int]
    plugin_type_code: str

    def validate(self):
        # FIXME: 一个 scope 只能绑定一种类型插件
        return

    def _get_scopes_display(self, scopes: List[Dict[str, Any]]) -> str:
        scopes_display = ", ".join([scope["name"] for scope in scopes[:3]])
        return scopes_display if len(scopes) <= 3 else scopes_display + "..."
