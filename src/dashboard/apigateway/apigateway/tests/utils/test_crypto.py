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
import pytest
from django.utils.encoding import smart_bytes, smart_str

from apigateway.utils.crypto import (
    KeyGenerator,
    KeyValidator,
    RSAKeyValidationError,
    get_public_key_from_private_key,
)


def test_get_public_key_from_private_key(fake_rsa_private_key, fake_rsa_public_key):
    result = get_public_key_from_private_key(fake_rsa_private_key)
    assert result.strip() == smart_bytes(fake_rsa_public_key.strip())


def test_get_public_key_from_private_key_error():
    with pytest.raises(RSAKeyValidationError):
        get_public_key_from_private_key("invalid-private-key")


class TestKeyGenerator:
    def test_generate_rsa_key(self):
        result = KeyGenerator().generate_rsa_key()

        assert "BEGIN RSA PRIVATE KEY" in smart_str(result[0])
        assert "BEGIN PUBLIC KEY" in smart_str(result[1])


class TestKeyValidator:
    def test_validate_rsa_key(self, fake_rsa_private_key, fake_rsa_public_key):
        KeyValidator().validate_rsa_key(smart_bytes(fake_rsa_private_key), smart_bytes(fake_rsa_public_key))

    def test_validate_rsa_key_error(self, fake_rsa_private_key):
        with pytest.raises(RSAKeyValidationError):
            KeyValidator().validate_rsa_key(smart_bytes(fake_rsa_private_key), smart_bytes("invalid-public-key"))

        with pytest.raises(RSAKeyValidationError):
            KeyValidator().validate_rsa_key(smart_bytes("invalid-private-key"), smart_bytes("invalid-public-key"))
