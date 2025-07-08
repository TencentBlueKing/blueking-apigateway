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
"""
创建 esb 相关网关，如 bk-esb、apigw
"""

import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from pydantic import TypeAdapter

from apigateway.biz.gateway import GatewayData, GatewaySaver
from apigateway.common.tenant.constants import (
    SELF_HOST_GATEWAY_DEFAULT_TENANT_ID,
    SELF_HOST_GATEWAY_DEFAULT_TENANT_MODE,
)
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)

    @transaction.atomic
    def handle(self, dry_run: bool, *args, **options):
        for name, config in getattr(settings, "SYNC_ESB_JWT_KEY_GATEWAY_NAMES", {}).items():
            gateway = get_object_or_None(Gateway, name=name)
            if gateway:
                logger.info("gateway [name=%s] already exists, skip", name)
                continue

            if not dry_run:
                tenant_mode = None
                tenant_id = None
                # assign the tenant_mode and tenant_id
                tenant_mode = SELF_HOST_GATEWAY_DEFAULT_TENANT_MODE
                tenant_id = SELF_HOST_GATEWAY_DEFAULT_TENANT_ID

                saver = GatewaySaver(
                    id=None,
                    data=TypeAdapter(GatewayData).validate_python(
                        dict(
                            config,
                            name=name,
                            maintainers=[settings.GATEWAY_DEFAULT_CREATOR],
                            status=GatewayStatusEnum.ACTIVE.value,
                            tenant_mode=tenant_mode,
                            tenant_id=tenant_id,
                        ),
                    ),
                    bk_app_code=settings.BK_APP_CODE,
                    username=settings.GATEWAY_DEFAULT_CREATOR,
                )
                saver.save()

        logger.info("create esb gateway [name=%s]", name)
