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
将 ESB 中的组件同步到网关，并且发布资源版本
"""
import logging

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.esb.component.constants import ESB_RELEASE_TASK_EXPIRES
from apigateway.apps.esb.component.tasks import sync_and_release_esb_components
from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--async", dest="async_", action="store_true", default=False, help="异步方式")
        parser.add_argument(
            "--access_token",
            dest="access_token for user when releasing esb to micro gateway",
            action="store",
            default="",
            help="access_token",
        )

    def handle(self, async_: bool, access_token: str = "", *args, **options):
        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        if not async_:
            sync_and_release_esb_components(esb_gateway.id, "admin", access_token, True)
            logger.info("sync and release esb components success")
            return

        apply_async_on_commit(
            sync_and_release_esb_components,
            args=(esb_gateway.id, "admin", access_token, True),
            expires=ESB_RELEASE_TASK_EXPIRES,
        )

        logger.info("sync and release esb components asynchronously, please check the release status on zhe web")
