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
from collections import defaultdict
from typing import Any, Dict, List, Optional

from attrs import define
from django.utils.translation import gettext as _

from apigateway.apps.access_strategy.constants import PLUGIN_TYPE_TO_STRATEGY_TYPE, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategyBinding
from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.biz.plugin_binding import PluginBindingHandler
from apigateway.core.models import Gateway


@define
class PluginBindingValidator:
    gateway: Gateway
    scope_type: PluginBindingScopeEnum
    scope_ids: List[int]
    plugin_type_code: str

    def validate(self):
        strategy_type = self._get_access_strategy_type(self.plugin_type_code)
        if not strategy_type:
            return

        access_strategy_bindings = AccessStrategyBinding.objects.query_scope_binding(
            api=self.gateway,
            scope_ids=self.scope_ids,
            scope_type=self.scope_type,
            access_strategy_type=strategy_type,
        )
        if not access_strategy_bindings:
            return

        name_to_scope_ids = defaultdict(list)
        for scope_id, access_strategies in access_strategy_bindings.items():
            for strategy in access_strategies:
                name_to_scope_ids[strategy["access_strategy_name"]].append(scope_id)

        access_strategy_name, scope_ids = name_to_scope_ids.popitem()
        scopes = PluginBindingHandler.get_scopes(self.gateway.pk, self.scope_type, scope_ids)
        raise ValueError(
            _("访问策略：{strategy_name}，已绑定到{scope_type_display}：{scopes_display}，请解绑后，再绑定插件，或联系管理员协助迁移。").format(
                strategy_name=access_strategy_name,
                scope_type_display=PluginBindingScopeEnum.get_choice_label(self.scope_type),
                scopes_display=self._get_scopes_display(scopes),
            )
        )

    def _get_access_strategy_type(self, type_code: str) -> Optional[AccessStrategyTypeEnum]:
        strategy_type = PLUGIN_TYPE_TO_STRATEGY_TYPE.get(type_code)
        if not strategy_type:
            return None

        return AccessStrategyTypeEnum(strategy_type)

    def _get_scopes_display(self, scopes: List[Dict[str, Any]]) -> str:
        scopes_display = ", ".join([scope["name"] for scope in scopes[:3]])
        return scopes_display if len(scopes) <= 3 else scopes_display + "..."
