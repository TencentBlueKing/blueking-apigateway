# -*- coding: utf-8 -*-
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
import base64
import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_str

from apigateway.core.models import Gateway
from apigateway.service.gateway_jwt import GatewayJWTHandler
from apigateway.utils.crypto import KeyValidator, RSAKeyValidationError
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """更新网关的 JWT 密钥"""

    def add_arguments(self, parser):
        parser.add_argument("--gateway-name", type=str, dest="gateway_name", required=True)
        parser.add_argument("--private-key", type=str, dest="private_key", required=True)
        parser.add_argument("--public-key", type=str, dest="public_key", required=True)

    def handle(self, gateway_name: str, private_key: str, public_key: str, **options):
        decoded_private_key = self._decode_base64(private_key).strip()
        decoded_public_key = self._decode_base64(public_key).strip()

        try:
            KeyValidator().validate_rsa_key(decoded_private_key, decoded_public_key)
        except RSAKeyValidationError as err:
            raise CommandError(str(err))

        gateway = get_object_or_None(Gateway, name=gateway_name)
        if not gateway:
            raise CommandError(f"gateway not found: gateway_name={gateway_name}")

        GatewayJWTHandler.update_jwt_key(gateway, decoded_private_key, decoded_public_key)

        logger.info(
            "update gateway jwt key success: gateway_name=%s, public_key=`%s`",
            gateway_name,
            smart_str(decoded_public_key),
        )

    def _decode_base64(self, encoded_key: str) -> bytes:
        try:
            return base64.b64decode(encoded_key)
        except Exception:  # pylint: disable=broad-except
            raise CommandError(f"not a valid base64 string: {encoded_key}")
