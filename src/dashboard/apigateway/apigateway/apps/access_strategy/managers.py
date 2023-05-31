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
from collections import defaultdict
from typing import Any, Dict, List, Optional

from django.db import models

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum


class IPGroupManager(models.Manager):
    pass


class AccessStrategyManager(models.Manager):
    def get_ids(self, gateway_id: int) -> List[int]:
        """获取指定网关下，所有访问策略的 ID 列表"""
        return list(self.filter(api_id=gateway_id).values_list("id", flat=True))

    def delete_strategies(self, access_strategy_ids):
        from apigateway.apps.access_strategy.models import AccessStrategyBinding

        # delete binding
        AccessStrategyBinding.objects.filter(access_strategy_id__in=access_strategy_ids).delete()

        # delete access-strategy
        self.filter(id__in=access_strategy_ids).delete()

    def delete_by_gateway_id(self, gateway_id):
        strategy_ids = list(self.filter(api_id=gateway_id).values_list("id", flat=True))
        if not strategy_ids:
            return

        self.delete_strategies(strategy_ids)

    def filter_strategy(self, api, _type=None, query=None, order_by=None, fuzzy=False):
        queryset = self.filter(api=api)

        if _type:
            queryset = queryset.filter(type=_type)

        # query 不是模型字段，仅支持模糊匹配，如需精确匹配，可使用具体字段
        if query and fuzzy:
            queryset = queryset.filter(name__contains=query)

        if order_by:
            queryset = queryset.order_by(order_by)

        return queryset


class AccessStrategyBindingManager(models.Manager):
    def query_scope_binding(
        self,
        api,
        scope_ids: List[int],
        scope_type: AccessStrategyBindScopeEnum,
        access_strategy_type: Optional[AccessStrategyTypeEnum] = None,
    ):
        """查询指定对象的已绑定访问策略的信息

        :return: scope_id 绑定的访问策略信息列表，例如：
            {
                1: [
                    {
                        "access_strategy_id": 1,
                        "access_strategy_name": "access_strategy_1",
                    }
                ]
            }
        """
        from apigateway.apps.access_strategy.models import AccessStrategy

        strategy_ids = AccessStrategy.objects.get_ids(api.pk)

        qs = self.filter(access_strategy_id__in=strategy_ids, scope_type=scope_type.value, scope_id__in=scope_ids)
        if access_strategy_type is not None:
            qs = qs.filter(access_strategy__type=access_strategy_type.value)

        bindings = qs.values("access_strategy__id", "access_strategy__name", "scope_id")

        scope_bindings: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for binding in bindings:
            scope_id = binding["scope_id"]
            scope_bindings[scope_id].append(
                {
                    "access_strategy_id": binding["access_strategy__id"],
                    "access_strategy_name": binding["access_strategy__name"],
                }
            )
        return scope_bindings

    def delete_by_scope_ids(self, scope_type, scope_ids):
        self.filter(scope_type=scope_type, scope_id__in=scope_ids).delete()

    def query_scope_id_to_bindings(
        self, gateway_id: int, scope_type: AccessStrategyBindScopeEnum, scope_ids: Optional[List[int]] = None
    ):
        """获取指定对象已绑定的策略绑定信息

        :return: scope_id 对应的策略绑定对象列表，例如
            {
                1: [AccessStrategyBinding1, AccessStrategyBinding2],
            }
        """
        from apigateway.apps.access_strategy.models import AccessStrategy

        strategy_ids = AccessStrategy.objects.get_ids(gateway_id)
        if not strategy_ids:
            return {}

        qs = self.filter(access_strategy_id__in=strategy_ids, scope_type=scope_type.value)
        if scope_ids is not None:
            qs = qs.filter(scope_id__in=scope_ids)

        scope_id_to_bindings = defaultdict(list)
        for binding in qs:
            scope_id_to_bindings[binding.scope_id].append(binding)

        return scope_id_to_bindings
