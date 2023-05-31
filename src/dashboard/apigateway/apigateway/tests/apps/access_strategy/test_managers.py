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
from ddf import G

from apigateway.apps.access_strategy.constants import AccessStrategyBindScopeEnum, AccessStrategyTypeEnum
from apigateway.apps.access_strategy.models import AccessStrategy, AccessStrategyBinding


class TestAccessStrategyManager:
    def test_get_ids(self, fake_gateway):
        strategy_1 = G(AccessStrategy, api=fake_gateway)
        strategy_2 = G(AccessStrategy, api=fake_gateway)
        ids = AccessStrategy.objects.get_ids(fake_gateway.id)
        assert set(ids) == {strategy_1.id, strategy_2.id}


class TestAccessStrategyBinding:
    def test_query_scope_binding(self, fake_gateway):
        s1 = G(AccessStrategy, api=fake_gateway, type="rate_limit")
        s2 = G(AccessStrategy, api=fake_gateway, type="cors")

        G(AccessStrategyBinding, scope_type="stage", scope_id=1, type="rate_limit", access_strategy=s1)
        G(AccessStrategyBinding, scope_type="stage", scope_id=2, type="cors", access_strategy=s2)

        result = AccessStrategyBinding.objects.query_scope_binding(
            fake_gateway, scope_ids=[1, 2], scope_type=AccessStrategyBindScopeEnum.STAGE
        )
        assert result == {
            1: [{"access_strategy_id": s1.id, "access_strategy_name": s1.name}],
            2: [{"access_strategy_id": s2.id, "access_strategy_name": s2.name}],
        }

        result = AccessStrategyBinding.objects.query_scope_binding(
            fake_gateway,
            scope_ids=[1, 2],
            scope_type=AccessStrategyBindScopeEnum.STAGE,
            access_strategy_type=AccessStrategyTypeEnum("rate_limit"),
        )
        assert result == {
            1: [{"access_strategy_id": s1.id, "access_strategy_name": s1.name}],
        }

    def test_query_scope_id_to_binding(self, fake_gateway):
        result = AccessStrategyBinding.objects.query_scope_id_to_bindings(
            gateway_id=fake_gateway.id, scope_type=AccessStrategyBindScopeEnum.STAGE
        )
        assert result == {}

        strategy_1 = G(AccessStrategy, api=fake_gateway, type="cors")
        strategy_2 = G(AccessStrategy, api=fake_gateway, type="rate_limit")
        binding1 = G(
            AccessStrategyBinding,
            scope_id=1,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            access_strategy=strategy_1,
            type="cors",
        )
        binding2 = G(
            AccessStrategyBinding,
            scope_id=1,
            scope_type=AccessStrategyBindScopeEnum.STAGE.value,
            access_strategy=strategy_2,
            type="rate_limit",
        )
        binding3 = G(
            AccessStrategyBinding,
            scope_id=1,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            access_strategy=strategy_1,
            type="cors",
        )
        binding4 = G(
            AccessStrategyBinding,
            scope_id=2,
            scope_type=AccessStrategyBindScopeEnum.RESOURCE.value,
            access_strategy=strategy_2,
            type="rate_limit",
        )

        result = AccessStrategyBinding.objects.query_scope_id_to_bindings(
            gateway_id=fake_gateway.id, scope_type=AccessStrategyBindScopeEnum.STAGE
        )
        assert result == {1: [binding1, binding2]}

        result = AccessStrategyBinding.objects.query_scope_id_to_bindings(
            gateway_id=fake_gateway.id, scope_type=AccessStrategyBindScopeEnum.RESOURCE
        )
        assert result == {1: [binding3], 2: [binding4]}

        result = AccessStrategyBinding.objects.query_scope_id_to_bindings(
            gateway_id=fake_gateway.id, scope_type=AccessStrategyBindScopeEnum.RESOURCE, scope_ids=[1]
        )
        assert result == {1: [binding3]}
