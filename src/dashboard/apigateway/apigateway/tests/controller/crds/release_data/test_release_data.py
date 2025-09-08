#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

import pytest
from ddf import G

from apigateway.apps.plugin.constants import PluginBindingScopeEnum
from apigateway.apps.plugin.models import PluginBinding
from apigateway.service.contexts import GatewayAuthContext
from apigateway.service.gateway_jwt import GatewayJWTHandler


class TestReleaseData:
    @pytest.fixture(autouse=True)
    def setup(self, fake_release_data):
        self.release_data = fake_release_data

    def test_gateway(self, edge_gateway):
        assert self.release_data.gateway == edge_gateway

    def test_stage(self, edge_gateway_stage):
        assert self.release_data.stage == edge_gateway_stage

    def test_resource_version(self, edge_resource_version):
        assert self.release_data.resource_version == edge_resource_version

    def test_jwt_private_key(self, edge_gateway):
        jwt_private_key = GatewayJWTHandler.get_private_key(edge_gateway.pk)
        assert self.release_data.jwt_private_key == jwt_private_key

    def test_gateway_auth_config(self, edge_gateway):
        gateway_auth_config = GatewayAuthContext().get_config(edge_gateway.pk)
        assert self.release_data.gateway_auth_config == gateway_auth_config

    def test_get_stage_plugins(self, edge_gateway, edge_gateway_stage, edge_plugin_config, edge_plugin_type):
        G(
            PluginBinding,
            gateway=edge_gateway,
            scope_type=PluginBindingScopeEnum.STAGE.value,
            scope_id=edge_gateway_stage.pk,
            config=edge_plugin_config,
        )

        plugins = self.release_data.get_stage_plugins()
        assert len(plugins) == 1

        # 环境同时绑定了频率控制访问策略和插件
        edge_plugin_type.code = "bk-rate-limit"
        edge_plugin_type.save()
        plugins = self.release_data.get_stage_plugins()
        assert len(plugins) == 1
        assert plugins[0].config == {"rates": {"__default": [{"period": 60, "tokens": 100}]}}
