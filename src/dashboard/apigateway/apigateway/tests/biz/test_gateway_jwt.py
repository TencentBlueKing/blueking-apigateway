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
from django.utils.encoding import smart_bytes

from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.common.mcryptography import AESCipherManager
from apigateway.core.models import JWT, Gateway


class TestGatewayJWTHandler:
    def test_create_jwt(self):
        gateway = G(Gateway)

        result = GatewayJWTHandler.create_jwt(gateway)
        assert result.gateway == gateway
        assert result.private_key == ""
        assert "BEGIN PUBLIC KEY" in result.public_key
        assert result.encrypted_private_key

    def test_update_jwt_key(self, faker):
        gateway = G(Gateway)
        jwt = G(JWT, gateway=gateway, private_key=faker.pystr(), public_key=faker.pystr())

        GatewayJWTHandler.update_jwt_key(gateway, "test", "test")
        jwt = JWT.objects.get(gateway=gateway)

        cipher = AESCipherManager.create_jwt_cipher()
        assert jwt.public_key == "test"
        assert cipher.decrypt_from_hex(jwt.encrypted_private_key) == "test"

    def test_get_private_key(self):
        gateway = G(Gateway)
        G(JWT, gateway=gateway)
        GatewayJWTHandler.update_jwt_key(gateway, "test", "test")
        assert GatewayJWTHandler.get_private_key(gateway.id) == "test"

    def test_is_jwt_key_changed(self, faker):
        gateway = G(Gateway)
        jwt = GatewayJWTHandler.create_jwt(gateway)

        assert GatewayJWTHandler.is_jwt_key_changed(
            gateway,
            smart_bytes(faker.pystr()),
            smart_bytes(faker.pystr()),
        )

        cipher = AESCipherManager.create_jwt_cipher()
        assert not GatewayJWTHandler.is_jwt_key_changed(
            gateway,
            cipher.decrypt_from_hex(jwt.encrypted_private_key),
            smart_bytes(jwt.public_key),
        )
