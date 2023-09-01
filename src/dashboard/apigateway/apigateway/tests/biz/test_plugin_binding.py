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
from apigateway.biz.plugin_binding import PluginBindingHandler
from apigateway.core.models import Resource, Stage


class TestPluginBindingHandler:
    def test_get_scopes(self, fake_gateway):
        s1 = G(Stage, gateway=fake_gateway)
        s2 = G(Stage, gateway=fake_gateway)

        r1 = G(Resource, gateway=fake_gateway)
        r2 = G(Resource, gateway=fake_gateway)

        result = PluginBindingHandler.get_scopes(
            gateway_id=fake_gateway.id, scope_type=PluginBindingScopeEnum.STAGE, scope_ids=[s1.id, s2.id]
        )
        result.sort(key=lambda x: x["id"])
        assert result == [{"id": s1.id, "name": s1.name}, {"id": s2.id, "name": s2.name}]

        result = PluginBindingHandler.get_scopes(
            gateway_id=fake_gateway.id, scope_type=PluginBindingScopeEnum.RESOURCE, scope_ids=[r1.id, r2.id]
        )
        result.sort(key=lambda x: x["id"])
        assert result == [{"id": r1.id, "name": r1.name}, {"id": r2.id, "name": r2.name}]
