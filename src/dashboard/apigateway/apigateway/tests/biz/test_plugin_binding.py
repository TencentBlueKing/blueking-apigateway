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
from apigateway.apps.plugin.models import PluginBinding, PluginConfig
from apigateway.biz.plugin_binding import PluginBindingHandler


class TestPluginBindingHandler:
    def test_delete_by_bindings(self, fake_gateway, echo_plugin_resource_binding):
        assert PluginConfig.objects.filter(gateway=fake_gateway).exists()
        assert PluginBinding.objects.filter(gateway=fake_gateway).exists()

        PluginBindingHandler.delete_by_bindings(fake_gateway.id, [echo_plugin_resource_binding])

        assert not PluginConfig.objects.filter(gateway=fake_gateway).exists()
        assert not PluginBinding.objects.filter(gateway=fake_gateway).exists()
