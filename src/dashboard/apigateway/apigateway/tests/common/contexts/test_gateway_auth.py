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
from apigateway.biz.gateway import GatewayHandler
from apigateway.common.contexts import GatewayAuthContext
from apigateway.core.constants import GatewayTypeEnum


class TestGatewayAuthContext:
    def test_get_gateway_id_to_auth_config(self, fake_gateway):
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        result = GatewayAuthContext().get_gateway_id_to_auth_config([fake_gateway.id])
        assert fake_gateway.id in result
        assert result[fake_gateway.id].gateway_type == GatewayTypeEnum.CLOUDS_API.value
        assert result[fake_gateway.id].allow_update_gateway_auth is True

    def test_get_auth_config(self, fake_gateway):
        GatewayHandler.save_auth_config(fake_gateway.id, "default")

        result = GatewayAuthContext().get_auth_config(fake_gateway.id)
        assert result.gateway_type == GatewayTypeEnum.CLOUDS_API.value
        assert result.allow_update_gateway_auth is True
