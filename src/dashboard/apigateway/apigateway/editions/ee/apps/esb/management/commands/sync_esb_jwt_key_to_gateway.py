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
"""
将 ESB 的 JWT 密钥同步到 API Gateway 网关 bk-esb, apigw
"""
import logging

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.encoding import smart_bytes

from apigateway.apps.esb.bkcore.models import FunctionController
from apigateway.biz.gateway_jwt import GatewayJWTHandler
from apigateway.core.models import Gateway
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)

    def handle(self, dry_run: bool, *args, **options):
        esb_jwt_key = FunctionController.objects.get_jwt_key()
        if not esb_jwt_key:
            raise CommandError("No esb jwt key found")

        for name in getattr(settings, "SYNC_ESB_JWT_KEY_GATEWAY_NAMES", {}):
            gateway = get_object_or_None(Gateway, name=name)
            if not gateway:
                logger.warning("Gateway %s not found, cannot sync esb jwt key", name)
                continue

            is_changed = GatewayJWTHandler.is_jwt_key_changed(
                gateway,
                smart_bytes(esb_jwt_key["private_key"]),
                smart_bytes(esb_jwt_key["public_key"]),
            )
            if not is_changed:
                continue

            if not dry_run:
                GatewayJWTHandler.update_jwt_key(
                    gateway,
                    smart_bytes(esb_jwt_key["private_key"]),
                    smart_bytes(esb_jwt_key["public_key"]),
                )

            logger.info("sync esb jwt key to gateway [name=%s]", name)
