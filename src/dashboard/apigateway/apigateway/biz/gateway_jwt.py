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
from django.utils.encoding import smart_str

from apigateway.common.mcryptography import AESCipherManager
from apigateway.core.models import JWT, Gateway
from apigateway.utils.crypto import KeyGenerator


class GatewayJWTHandler:
    @staticmethod
    def create_jwt(gateway: Gateway) -> JWT:
        private_key, public_key = KeyGenerator().generate_rsa_key()
        cipher = AESCipherManager.create_jwt_cipher()
        return JWT.objects.create(
            gateway=gateway,
            # 使用加密数据，不保存明文的 private_key
            # private_key=smart_str(private_key),
            private_key="",
            public_key=smart_str(public_key),
            encrypted_private_key=cipher.encrypt_to_hex(smart_str(private_key)),
        )

    @staticmethod
    def update_jwt_key(gateway, private_key: bytes, public_key: bytes):
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = JWT.objects.get(gateway=gateway)
        jwt.public_key = smart_str(public_key)
        jwt.encrypted_private_key = cipher.encrypt_to_hex(smart_str(private_key))
        jwt.save(update_fields=["public_key", "encrypted_private_key"])

    @staticmethod
    def get_private_key(gateway_id: int) -> str:
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = JWT.objects.get(gateway_id=gateway_id)
        return cipher.decrypt_from_hex(jwt.encrypted_private_key)

    @staticmethod
    def is_jwt_key_changed(gateway, private_key: bytes, public_key: bytes) -> bool:
        cipher = AESCipherManager.create_jwt_cipher()

        jwt = JWT.objects.get(gateway=gateway)
        return jwt.public_key != smart_str(public_key) or cipher.decrypt_from_hex(
            jwt.encrypted_private_key
        ) != smart_str(private_key)
