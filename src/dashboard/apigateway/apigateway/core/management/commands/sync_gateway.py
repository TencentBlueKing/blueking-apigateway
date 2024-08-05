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

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from apigateway.biz.gateway.saver import GatewayData, GatewaySaver
from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """同步网关

    如果网关不存在，则创建网关
    如果网关已存在，则更新指定网关的配置
    """

    def add_arguments(self, parser):
        parser.add_argument("--name", type=str, dest="name", required=True)

    @transaction.atomic
    def handle(self, name: str, **options):
        gateway = get_object_or_None(Gateway, name=name)
        if gateway:
            logger.info("gateway[name=%s] has exist not need update", name)
            return
        saver = GatewaySaver(
            id=None,
            data=GatewayData(
                name=name,
                maintainers=[settings.GATEWAY_DEFAULT_CREATOR],
                status=GatewayStatusEnum.ACTIVE.value,
                is_public=False,
            ),
            username=settings.GATEWAY_DEFAULT_CREATOR,
        )
        saver.save()
        logger.info("sync gateway success: name=%s", name)
