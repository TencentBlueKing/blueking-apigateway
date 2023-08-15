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
from dataclasses import dataclass, field
from typing import List, Set

from django.db.models import Q

from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.core.models import Gateway


@dataclass
class PluginBindingPlan:
    """用于描述请求的绑定会如何应用到现有的插件绑定中"""

    config: PluginConfig
    # 处理绑定
    handle_bind: bool = True
    # 处理解绑
    handle_unbind: bool = True
    # 更新的字段
    update_fields: Set[str] = field(default_factory=set)
    # 最终的绑定
    binds: List[PluginBinding] = field(default_factory=list)
    # 未指定因此被删除的
    unbinds: List[PluginBinding] = field(default_factory=list)
    # 同类型插件被覆盖的，相当于删除但含义不同
    overwrites: List[PluginBinding] = field(default_factory=list)
    # 新增的绑定
    creates: List[PluginBinding] = field(default_factory=list)

    def _update(self, queryset, requested_bindings):
        related_bindings = {i.scope_id: i for i in queryset}
        for scope_id, binding in requested_bindings.items():
            related_binding = related_bindings.pop(scope_id, None)

            if not self.handle_bind:
                continue

            if related_binding is None:
                # to create (append binding directly, see below)
                self.creates.append(binding)
            elif related_binding.config_id != binding.config_id:
                # to overwrite, update by id
                binding.pk = related_binding.pk
                self.overwrites.append(related_binding)
            else:
                # to update (by id)
                binding.pk = related_binding.pk

            # all the requested bindings need to be bind
            self.binds.append(binding)

        if self.handle_unbind:
            # to delete
            self.unbinds.extend(related_bindings.values())

    def _make_requested_bindings(
        self,
        gateway: Gateway,
        config: PluginConfig,
        scope_type: str,
        scope_ids: List[int],
        **kwargs,
    ):
        self.update_fields.update(kwargs.keys())
        self.update_fields.update(
            [
                "gateway",
                "plugin",
                "scope_type",
                "scope_id",
                "config",
                "updated_time",
            ]
        )
        return {
            i: PluginBinding(
                gateway=gateway,
                config=config,
                scope_type=scope_type,
                scope_id=i,
                **kwargs,
            )
            for i in scope_ids
        }

    def update_for_bind(
        self,
        queryset,
        scope_type: str,
        scope_ids: List[int],
        **kwargs,
    ):
        gateway = self.config.gateway
        config = self.config
        # 有相同插件配置绑定的（分析增加和删除）
        q_bindings_with_same_config = Q(config=config)
        # 指定对象已绑定相同类型的（分析覆盖）
        q_related_bindings_to_overwrites = Q(config__type_id=config.type_id, scope_id__in=scope_ids)
        self._update(
            queryset.filter(gateway=gateway, scope_type=scope_type).filter(
                q_bindings_with_same_config | q_related_bindings_to_overwrites
            ),
            self._make_requested_bindings(
                gateway=gateway,
                config=config,
                scope_type=scope_type,
                scope_ids=scope_ids,
                **kwargs,
            ),
        )

        return self

    def update_for_unbind(
        self,
        queryset,
        scope_type: str,
        scope_ids: List[int],
        **kwargs,
    ):
        gateway = self.config.gateway
        self._update(
            queryset.filter(gateway=gateway, config=self.config, scope_type=scope_type, scope_id__in=scope_ids),
            {},
        )

        return self
