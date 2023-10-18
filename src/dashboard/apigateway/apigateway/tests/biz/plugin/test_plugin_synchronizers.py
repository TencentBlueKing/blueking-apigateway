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

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding, PluginConfig, PluginType
from apigateway.biz.plugin.plugin_synchronizers import PluginConfigData, PluginSynchronizer


class TestPluginSynchronizer:
    def test_sync(self, fake_gateway):
        type_1 = G(PluginType, schema=None)
        type_2 = G(PluginType, schema=None)

        scope_id_to_plugin_configs = {
            1: [PluginConfigData(type=type_1.code, yaml="foo"), PluginConfigData(type=type_2.code, yaml="bar")],
            2: [PluginConfigData(type=type_1.code, yaml="baz")],
        }

        synchronizer = PluginSynchronizer()

        # add
        synchronizer.sync(
            gateway_id=fake_gateway.id,
            scope_type=PluginBindingScopeEnum.RESOURCE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )

        assert PluginConfig.objects.filter(gateway=fake_gateway).count() == 3
        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 3

        # update
        synchronizer.sync(
            gateway_id=fake_gateway.id,
            scope_type=PluginBindingScopeEnum.RESOURCE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )

        assert PluginConfig.objects.filter(gateway=fake_gateway).count() == 3
        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 3

        # delete
        scope_id_to_plugin_configs = {
            1: [PluginConfigData(type=type_1.code, yaml="another")],
            2: [],
        }
        synchronizer.sync(
            gateway_id=fake_gateway.id,
            scope_type=PluginBindingScopeEnum.RESOURCE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )

        assert PluginConfig.objects.filter(gateway=fake_gateway).count() == 1
        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 1
        assert PluginConfig.objects.get(gateway=fake_gateway).yaml == "another"

        # do nothing
        scope_id_to_plugin_configs = {}
        synchronizer.sync(
            gateway_id=fake_gateway.id,
            scope_type=PluginBindingScopeEnum.RESOURCE,
            scope_id_to_plugin_configs=scope_id_to_plugin_configs,
        )

        assert PluginConfig.objects.filter(gateway=fake_gateway).count() == 1
        assert PluginBinding.objects.filter(gateway=fake_gateway).count() == 1
