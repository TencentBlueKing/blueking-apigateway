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
from apigateway.biz.gateway_app_binding import GatewayAppBindingHandler
from apigateway.core.models import GatewayAppBinding


class TestGatewayAppBindingHandler:
    def test_update_gateway_app_bindings(self, fake_gateway):
        GatewayAppBindingHandler.update_gateway_app_bindings(fake_gateway, ["app1", "app2"])
        assert GatewayAppBinding.objects.filter(gateway=fake_gateway).count() == 2

        GatewayAppBindingHandler.update_gateway_app_bindings(fake_gateway, ["app3", "app2"])
        assert GatewayAppBinding.objects.filter(gateway=fake_gateway).count() == 2

        GatewayAppBindingHandler.update_gateway_app_bindings(fake_gateway, ["app1"])
        assert GatewayAppBinding.objects.filter(gateway=fake_gateway).count() == 1

        GatewayAppBindingHandler.update_gateway_app_bindings(fake_gateway, [])
        assert GatewayAppBinding.objects.filter(gateway=fake_gateway).count() == 0

    def test_get_bound_app_codes(self, fake_gateway):
        GatewayAppBindingHandler.update_gateway_app_bindings(fake_gateway, ["app1", "app2"])
        result = GatewayAppBindingHandler.get_bound_app_codes(gateway=fake_gateway)
        assert set(result) == {"app1", "app2"}
