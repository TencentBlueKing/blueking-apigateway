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
import logging

from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_str

from apigateway.core.models import JWT, Gateway
from apigateway.utils.crypto import KeyValidator, RSAKeyValidationError
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """更新网关的 JWT 密钥"""

    def add_arguments(self, parser):
        parser.add_argument("--api-name", type=str, dest="api_name", required=True)
        parser.add_argument("--private-key", type=str, dest="private_key", required=True)
        parser.add_argument("--public-key", type=str, dest="public_key", required=True)

    def handle(self, api_name: str, private_key: str, public_key: str, **options):
        decoded_private_key = self._decode_base64(private_key).strip()
        decoded_public_key = self._decode_base64(public_key).strip()

        try:
            KeyValidator().validate_rsa_key(decoded_private_key, decoded_public_key)
        except RSAKeyValidationError as err:
            raise CommandError(str(err))

        gateway = get_object_or_None(Gateway, name=api_name)
        if not gateway:
            raise CommandError(f"gateway not found: gateway_name={api_name}")

        JWT.objects.update_jwt_key(gateway, decoded_private_key, decoded_public_key)

        logger.info(
            f"update gateway jwt key success: gateway_name={api_name}, public_key=`{smart_str(decoded_public_key)}`"
        )

    def _decode_base64(self, encoded_key: str) -> bytes:
        try:
            return base64.b64decode(encoded_key)
        except Exception:
            raise CommandError(f"not a valid base64 string: {encoded_key}")
