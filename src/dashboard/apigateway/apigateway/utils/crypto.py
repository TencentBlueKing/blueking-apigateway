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
import base64
import hashlib
from typing import Tuple, Union

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from django.utils.encoding import force_bytes


class RSAKeyValidationError(Exception):
    """RSA 密钥校验失败"""


def get_public_key_from_private_key(pem_private_key: Union[str, bytes]) -> bytes:
    try:
        private_key = serialization.load_pem_private_key(force_bytes(pem_private_key), password=None)
    except Exception as err:
        raise RSAKeyValidationError(str(err))

    return private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
    )


class KeyGenerator:
    def generate_rsa_key(self, length=2048) -> Tuple[bytes, bytes]:
        """
        生成一个新的密钥
        """
        # public_exponent: The public exponent of the new key. Either 65537 or 3 (for legacy purposes).
        # Almost everyone should use 65537.
        # more: https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#generation
        key = rsa.generate_private_key(public_exponent=65537, key_size=length)

        private_key = key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption(),
        )

        public_key = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )

        return (private_key.strip(), public_key.strip())


class KeyValidator:
    def validate_rsa_key(self, private_key: bytes, public_key: bytes):
        """
        校验 RSA 密钥

        - https://cryptography.io/en/latest/hazmat/primitives/asymmetric/rsa/#key-loading
        """
        expected_public_key = get_public_key_from_private_key(private_key)
        if expected_public_key.strip() != public_key:
            raise RSAKeyValidationError("public key not match")


def calculate_fingerprint(content):
    """
    For specification, see RFC4716, section 4
    """
    key = base64.b64decode("".join(content.splitlines()[1:-1]).encode("ascii"))
    fp_plain = hashlib.md5(key).hexdigest()
    return ":".join(a + b for a, b in zip(fp_plain[::2], fp_plain[1::2]))
