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
import logging
import uuid
from typing import Optional

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from rest_framework import serializers

from apigateway.common.factories import SchemaFactory
from apigateway.controller.micro_gateway_config import MicroGatewayHTTPInfo, MicroGatewayJWTAuth
from apigateway.core import constants
from apigateway.core.models import Gateway, MicroGateway, Stage
from apigateway.utils.string import generate_unique_id

logger = logging.getLogger(__name__)


class ArgumentSLZ(serializers.Serializer):
    stage_name = serializers.RegexField(constants.STAGE_NAME_PATTERN, required=True)
    micro_gateway_name = serializers.RegexField(constants.MICRO_GATEWAY_NAME_PATTERN, required=True)
    micro_gateway_id = serializers.UUIDField(required=False)


class Command(BaseCommand):
    """同步默认网关"""

    def add_arguments(self, parser):
        parser.add_argument("--gateway", dest="gateway_name", required=True, help="default gateway name")
        parser.add_argument("--stage", dest="stage_name", required=True, help="default stage name")
        parser.add_argument("--name", dest="micro_gateway_name", required=True, help="default micro-gateway name")
        parser.add_argument(
            "--instance-id",
            dest="micro_gateway_id",
            default=settings.DEFAULT_MICRO_GATEWAY_ID,
            help="micro gateway instance id",
        )
        parser.add_argument(
            "--secret",
            dest="secret_key",
            default=None,
            help="The `secret_key` in the config, using a UUID hex string if absent, will always be"
            " ignored if an old value exists on the old config object. This means modification is not supported.",
        )
        parser.add_argument("--http-url", dest="http_url", required=True, help="default http url")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def sync_micro_gateway(
        self, gateway: Gateway, stage_name: str, micro_gateway_name: str, micro_gateway_id: uuid.UUID
    ):
        micro_gateway, _ = MicroGateway.objects.update_or_create(
            id=micro_gateway_id,
            defaults={
                "is_shared": True,
                "is_managed": False,  # 默认共享实例是整体一起部署的，所以肯定不是 dashboard 管理的
                "name": micro_gateway_name,
                "status": constants.MicroGatewayStatusEnum.UPDATED.value,
                "schema": SchemaFactory().get_micro_gateway_schema(),
                "gateway": gateway,
            },
        )

        stage = Stage.objects.get(gateway=gateway, name=stage_name)
        stage.micro_gateway = micro_gateway
        stage.save(update_fields=["micro_gateway"])

        return micro_gateway

    @transaction.atomic()
    def handle(self, secret_key: Optional[str], gateway_name: str, http_url: str, dry_run: bool, **kwargs):
        # FIXME: why slz here?
        slz = ArgumentSLZ(data=kwargs)
        slz.is_valid(raise_exception=True)

        gateway = Gateway.objects.get(name=gateway_name)
        micro_gateway = self.sync_micro_gateway(
            gateway=gateway,
            stage_name=slz.validated_data["stage_name"],
            micro_gateway_name=slz.validated_data["micro_gateway_name"],
            micro_gateway_id=slz.validated_data["micro_gateway_id"],
        )

        micro_gateway_config = micro_gateway.config

        # Mutate the existing config based on current parameters.
        # key: "http_info"(always replace)
        http_info = MicroGatewayHTTPInfo.from_micro_gateway_config(micro_gateway_config)
        http_info.http_url = http_url
        micro_gateway_config.update(http_info.to_micro_gateway_config())

        # key: "secret_key"(modify not supported)
        jwt_auth = MicroGatewayJWTAuth.from_micro_gateway_config(micro_gateway_config)
        self.set_secret_key_if_empty(jwt_auth, secret_key)
        micro_gateway_config.update(jwt_auth.to_micro_gateway_config())

        micro_gateway.config = micro_gateway_config
        micro_gateway.save()

        logger.info("micro-gateway synced, id: %s", micro_gateway.id)
        if dry_run:
            transaction.savepoint_rollback(transaction.savepoint())

    def set_secret_key_if_empty(self, auth_obj: MicroGatewayJWTAuth, secret_key: Optional[str]):
        """Set the `secret_key` field only if the old value is absent."""
        if auth_obj.secret_key:
            # Print a log message to notify the user when a secret key is specified.
            if secret_key:
                self.stdout.write(
                    'Skip updating existing "secret_key" because it is not supported.', self.style.WARNING
                )
                return
            return

        # The "secret_key" is absent or empty, replace it
        secret_key = secret_key or generate_unique_id()
        auth_obj.secret_key = secret_key
