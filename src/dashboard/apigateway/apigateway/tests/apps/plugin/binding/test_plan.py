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

from apigateway.apps.plugin.binding.plan import PluginBindingPlan
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType


class TestPluginBindingPlan:
    def test_update(self, fake_gateway, fake_plugin_type):
        config1 = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type)
        config2 = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=2, config=config2)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=3, config=config1)

        plan = PluginBindingPlan(config=config1)
        requested_bindings = plan._make_requested_bindings(
            gateway=fake_gateway,
            config=config1,
            scope_type="resource",
            # 1 create, 2 override, 3 delete
            scope_ids=[1, 2],
        )
        queryset = PluginBinding.objects.filter(gateway=fake_gateway, scope_type="resource")

        # not handle bind/unbind
        plan.handle_bind = False
        plan.handle_unbind = False
        plan._update(queryset, requested_bindings)
        assert not plan.binds
        assert not plan.unbinds
        assert not plan.overwrites
        assert not plan.creates

        # handle bind/unbind
        plan.handle_bind = True
        plan.handle_unbind = True
        plan._update(queryset, requested_bindings)
        assert len(plan.binds) == 2
        assert len(plan.unbinds) == 1
        assert len(plan.overwrites) == 1
        assert len(plan.creates) == 1
        assert plan.unbinds[0].scope_id == 3
        assert plan.overwrites[0].scope_id == 2

    def test_update_for_bind(self, fake_gateway, fake_plugin_type):
        config1 = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type)
        config2 = G(PluginConfig, gateway=fake_gateway, type=fake_plugin_type)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=2, config=config2)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=3, config=config1)
        G(PluginBinding, gateway=fake_gateway, scope_type="stage", scope_id=2, config=config2)
        G(PluginBinding, gateway=fake_gateway, scope_type="stage", scope_id=3, config=config1)

        plan = PluginBindingPlan(config=config1)
        queryset = PluginBinding.objects.filter(gateway=fake_gateway)
        plan.update_for_bind(queryset, scope_type="resource", scope_ids=[1, 2])

        assert len(plan.binds) == 2
        assert len(plan.unbinds) == 1
        assert len(plan.overwrites) == 1
        assert len(plan.creates) == 1
        assert plan.unbinds[0].scope_id == 3
        assert plan.unbinds[0].scope_type == "resource"
        assert plan.overwrites[0].scope_id == 2
        assert plan.overwrites[0].scope_type == "resource"
        assert plan.creates[0].scope_id == 1
        assert plan.creates[0].scope_type == "resource"

    def test_update_for_unbind(self, fake_gateway):
        type1 = G(PluginType)
        type2 = G(PluginType)
        config1 = G(PluginConfig, gateway=fake_gateway, type=type1)
        config2 = G(PluginConfig, gateway=fake_gateway, type=type2)

        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=1, config=config1)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=2, config=config1)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=2, config=config2)
        G(PluginBinding, gateway=fake_gateway, scope_type="resource", scope_id=1, config=config2)
        G(PluginBinding, gateway=fake_gateway, scope_type="stage", scope_id=1, config=config1)
        G(PluginBinding, gateway=fake_gateway, scope_type="stage", scope_id=1, config=config2)

        plan = PluginBindingPlan(config=config2)
        queryset = PluginBinding.objects.filter(gateway=fake_gateway)
        plan.update_for_unbind(queryset, scope_type="resource", scope_ids=[1, 2])

        assert len(plan.binds) == 0
        assert len(plan.unbinds) == 2
        assert len(plan.overwrites) == 0
        assert len(plan.creates) == 0
        assert plan.unbinds[0].scope_id in [1, 2]
        assert plan.unbinds[1].scope_id in [1, 2]
        assert plan.unbinds[0].scope_type == "resource"
        assert plan.unbinds[1].scope_type == "resource"
        assert plan.unbinds[0].config == config2
        assert plan.unbinds[1].config == config2
