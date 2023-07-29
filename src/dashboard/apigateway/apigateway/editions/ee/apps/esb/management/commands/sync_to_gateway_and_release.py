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
from typing import Optional

from blue_krill.async_utils.django_utils import apply_async_on_commit
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.esb.component.constants import ESB_RELEASE_TASK_EXPIRES
from apigateway.apps.esb.component.tasks import sync_and_release_esb_components
from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.core.models import Gateway, Release
from apigateway.utils.conv import str_bool

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    将 ESB 中的组件同步到网关，并且发布资源版本

    - 如果未通过 async 指定同步方式，则
      - 如果 bk-esb 网关未发布，则采用同步方式，同步后接口即可访问
      - 如果 bk-esb 网关已发布，则采用异步方式，减少部署耗时
    """

    def add_arguments(self, parser):
        parser.add_argument("--async", dest="async_", type=str_bool, help="异步方式，可选值：true, false")
        parser.add_argument(
            "--access_token",
            dest="access_token for user when releasing esb to micro gateway",
            action="store",
            default="",
            help="access_token",
        )

    def handle(self, async_: Optional[bool], access_token: str = "", *args, **options):
        print(f"sync esb components to gateway(name={settings.BK_ESB_GATEWAY_NAME}) start")

        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        if not self._use_async(async_, esb_gateway):
            print(
                f"sync esb components to gateway(name={settings.BK_ESB_GATEWAY_NAME}) synchronously, "
                "please wait a few minutes"
            )
            sync_and_release_esb_components(esb_gateway.id, "admin", access_token, True)
            print(f"sync esb components to gateway(name={settings.BK_ESB_GATEWAY_NAME}) and release successfully")
            return

        apply_async_on_commit(
            sync_and_release_esb_components,
            args=(esb_gateway.id, "admin", access_token, True),
            expires=ESB_RELEASE_TASK_EXPIRES,
        )

        print(
            f"sync esb components to gateway(name={settings.BK_ESB_GATEWAY_NAME}) and release asynchronously, "
            "please check the release result on the website"
        )

    def _use_async(self, async_: Optional[bool], gateway: Gateway) -> bool:
        if async_ is not None:
            return async_

        # 未指定时，如果网关未发布，采用同步方式，以确保同步后接口即可访问
        return Release.objects.filter(api=gateway).exists()
