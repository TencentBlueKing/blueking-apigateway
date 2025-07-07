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
from blue_krill.encrypt.handler import EncryptHandler
from django.conf import settings
from django.utils.encoding import force_bytes, smart_str

from apigateway.common.encrypt.cipher import AESGCMCipher
from apigateway.core.models import JWT, Gateway
from apigateway.utils.crypto import KeyGenerator


class CustomCrypto:
    def __init__(self):
        self._jwt_cipher = AESGCMCipher(
            force_bytes(settings.JWT_CRYPTO_KEY),
            force_bytes(settings.CRYPTO_NONCE),
        )

    def encrypt(self, plaintext) -> str:
        return self._jwt_cipher.encrypt_to_hex(plaintext)

    def decrypt(self, encrypted_text) -> str:
        return self._jwt_cipher.decrypt_from_hex(encrypted_text)


class BkCrypto:
    def __init__(self):
        self._encrypt_handler = EncryptHandler(
            encrypt_cipher_type=settings.ENCRYPT_CIPHER_TYPE,
            secret_key=settings.BKKRILL_ENCRYPT_SECRET_KEY,
        )

    def encrypt(self, plaintext) -> str:
        return self._encrypt_handler.encrypt(plaintext)

    def decrypt(self, encrypted_text) -> str:
        return self._encrypt_handler.decrypt(encrypted_text)


def get_jwt_crypto():
    if settings.BK_CRYPTO_TYPE == settings.CRYPTO_TYPE_APIGW_CUSTOM:
        return CustomCrypto()
    if settings.BK_CRYPTO_TYPE in ("SHANGMI", "CLASSIC"):
        return BkCrypto()

    raise ValueError(f"Unknown encrypt cipher type: {settings.BK_CRYPTO_TYPE}")


class GatewayJWTHandler:
    @staticmethod
    def create_jwt(gateway: Gateway) -> JWT:
        private_key, public_key = KeyGenerator().generate_rsa_key()

        crypto = get_jwt_crypto()

        return JWT.objects.create(
            gateway=gateway,
            # 使用加密数据，不保存明文的 private_key
            # private_key=smart_str(private_key),
            private_key="",
            public_key=smart_str(public_key),
            encrypted_private_key=crypto.encrypt(smart_str(private_key)),
        )

    @staticmethod
    def update_jwt_key(gateway, private_key: bytes, public_key: bytes):
        crypto = get_jwt_crypto()

        jwt = JWT.objects.get(gateway=gateway)
        jwt.public_key = smart_str(public_key)
        jwt.encrypted_private_key = crypto.encrypt(smart_str(private_key))
        jwt.save(update_fields=["public_key", "encrypted_private_key"])

    @staticmethod
    def get_private_key(gateway_id: int) -> str:
        crypto = get_jwt_crypto()

        jwt = JWT.objects.get(gateway_id=gateway_id)
        return crypto.decrypt(jwt.encrypted_private_key)

    @staticmethod
    def is_jwt_key_changed(gateway, private_key: bytes, public_key: bytes) -> bool:
        crypto = get_jwt_crypto()

        jwt = JWT.objects.get(gateway=gateway)
        return jwt.public_key != smart_str(public_key) or crypto.decrypt(jwt.encrypted_private_key) != smart_str(
            private_key
        )
