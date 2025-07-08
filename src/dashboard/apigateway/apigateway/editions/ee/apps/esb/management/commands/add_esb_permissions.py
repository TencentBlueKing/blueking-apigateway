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
为应用添加访问 ESB 的权限
"""

import logging
from typing import List

from django.core.management.base import BaseCommand, CommandError

from apigateway.apps.esb.exceptions import EsbGatewayNotFound
from apigateway.apps.esb.utils import get_esb_gateway
from apigateway.apps.permission.models import AppGatewayPermission
from apigateway.biz.constants import APP_CODE_PATTERN
from apigateway.common.time import calculate_expires

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--bk-app-codes", dest="bk_app_codes", type=str, nargs="*")

    def handle(self, bk_app_codes: List[str], *args, **options):
        try:
            esb_gateway = get_esb_gateway()
        except EsbGatewayNotFound as err:
            raise CommandError(str(err))

        for bk_app_code in bk_app_codes:
            if not APP_CODE_PATTERN.match(bk_app_code):
                raise CommandError(f"bk_app_code [{bk_app_code}] does not match the required pattern")

            AppGatewayPermission.objects.get_or_create(
                bk_app_code=bk_app_code,
                gateway=esb_gateway,
                defaults={
                    "expires": calculate_expires(None),
                },
            )
