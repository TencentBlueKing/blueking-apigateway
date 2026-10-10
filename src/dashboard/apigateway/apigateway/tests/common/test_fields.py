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
import pytest
from bkcrypto import constants as bkcrypto_constants
from bkcrypto.asymmetric import options as bkcrypto_options
from bkcrypto.contrib.basic.ciphers import get_asymmetric_cipher
from rest_framework import serializers

from apigateway.common.fields import DecryptableCharField

SM2 = bkcrypto_constants.AsymmetricCipherType.SM2.value


class _SLZ(serializers.Serializer):
    password = DecryptableCharField(allow_blank=True, required=True)


class TestDecryptableCharField:
    @pytest.fixture
    def cipher(self, settings):
        cipher = get_asymmetric_cipher(cipher_type=SM2)
        settings.ENABLE_FRONTEND_ENCRYPT = True
        settings.FRONTEND_ENCRYPT_PUBLIC_KEY = cipher.export_public_key()
        settings.FRONTEND_ENCRYPT_PRIVATE_KEY = cipher.export_private_key()
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
        another = get_asymmetric_cipher(
            cipher_type=SM2,
            cipher_options={SM2: bkcrypto_options.SM2AsymmetricOptions()},
        )
        slz = _SLZ(data={"password": self._encrypted(another.encrypt("secret-password"))})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "decrypt_failed"

    def test_encrypted_when_disabled(self, cipher, settings):
        encrypted_value = cipher.encrypt("secret-password")
        settings.ENABLE_FRONTEND_ENCRYPT = False
        slz = _SLZ(data={"password": self._encrypted(encrypted_value)})
        assert not slz.is_valid()
        assert slz.errors["password"][0].code == "decrypt_failed"
