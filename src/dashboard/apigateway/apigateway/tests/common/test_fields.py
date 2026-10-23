# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from rest_framework import serializers

from apigateway.common.fields import DecryptableCharField
from apigateway.utils.crypto import KeyGenerator


class _Cipher:
    """模拟前端：使用公钥做 RSA-OAEP(SHA-256) 加密，输出 Base64"""

    def __init__(self):
        self.private_key, self.public_key = (key.decode() for key in KeyGenerator().generate_rsa_key())

    def encrypt(self, plaintext: str, algorithm: hashes.HashAlgorithm | None = None) -> str:
        oaep = self._oaep(algorithm or hashes.SHA256())
        return base64.b64encode(self._public_key().encrypt(plaintext.encode(), oaep)).decode()

    def encrypt_pkcs1v15(self, plaintext: str) -> str:
        return base64.b64encode(self._public_key().encrypt(plaintext.encode(), padding.PKCS1v15())).decode()

    def _public_key(self):
        return serialization.load_pem_public_key(self.public_key.encode())

    def _oaep(self, algorithm: hashes.HashAlgorithm) -> padding.OAEP:
        return padding.OAEP(mgf=padding.MGF1(algorithm), algorithm=algorithm, label=None)


class _SLZ(serializers.Serializer):
    password = DecryptableCharField(allow_blank=True, required=True)


class TestDecryptableCharField:
    @pytest.fixture
    def cipher(self, settings):
        cipher = _Cipher()
        settings.ENABLE_FRONTEND_ENCRYPT = True
        settings.FRONTEND_ENCRYPT_PUBLIC_KEY = cipher.public_key
        settings.FRONTEND_ENCRYPT_PRIVATE_KEY = cipher.private_key
        return cipher

    def _encrypted(self, value):
        return {"_encrypted": True, "_encrypted_value": value}

    @pytest.mark.parametrize("value", ["secret-password", ""])
    def test_plaintext(self, cipher, value):
        slz = _SLZ(data={"password": value})
        slz.is_valid(raise_exception=True)
        assert slz.validated_data["password"] == value

    def test_encrypted(self, cipher):
        slz = _SLZ(data={"password": self._encrypted(cipher.encrypt("secret-password"))})
        slz.is_valid(raise_exception=True)
        assert slz.validated_data["password"] == "secret-password"

    @pytest.mark.parametrize("value", ["", "中文密码", "x" * 190])
    def test_encrypted_utf8_and_single_block_boundary(self, cipher, value):
        slz = _SLZ(data={"password": self._encrypted(cipher.encrypt(value))})
        slz.is_valid(raise_exception=True)
        assert slz.validated_data["password"] == value

    def test_reject_multiple_rsa_blocks(self, cipher):
        block = base64.b64decode(cipher.encrypt("secret-password"))
        slz = _SLZ(data={"password": self._encrypted(base64.b64encode(block * 2).decode())})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "decrypt_failed"

    @pytest.mark.parametrize(
        "value",
        [
            {},
            {"_encrypted": False, "_encrypted_value": "abc"},
            {"_encrypted": "true", "_encrypted_value": "abc"},
            {"_encrypted": True},
            {"_encrypted": True, "_encrypted_value": ""},
            {"_encrypted": True, "_encrypted_value": 1},
        ],
    )
    def test_invalid_encrypted_value(self, cipher, value):
        slz = _SLZ(data={"password": value})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "invalid_encrypted_value"

    @pytest.mark.parametrize("encrypted_value", ["not-base64!", "YWJj"])
    def test_decrypt_failed(self, cipher, caplog, encrypted_value):
        slz = _SLZ(data={"password": self._encrypted(encrypted_value)})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "decrypt_failed"
        assert encrypted_value not in str(slz.errors) + caplog.text

    def test_decrypt_with_another_key(self, cipher):
        slz = _SLZ(data={"password": self._encrypted(_Cipher().encrypt("secret-password"))})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "decrypt_failed"

    def test_decrypt_with_another_scheme(self, cipher):
        for encrypted_value in [
            cipher.encrypt("secret-password", hashes.SHA1()),
            cipher.encrypt_pkcs1v15("secret-password"),
        ]:
            slz = _SLZ(data={"password": self._encrypted(encrypted_value)})
            assert not slz.is_valid()
            assert slz.errors["password"][0].code == "decrypt_failed"

    def test_encrypted_when_disabled(self, cipher, settings, caplog):
        encrypted_value = cipher.encrypt("secret-password")
        settings.ENABLE_FRONTEND_ENCRYPT = False
        slz = _SLZ(data={"password": self._encrypted(encrypted_value)})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "decrypt_failed"
        assert "frontend encrypt is disabled" in caplog.text
        assert encrypted_value not in caplog.text
