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

from django.core.management.base import BaseCommand

from apigateway.core import constants
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """更新网关 hosting_type 配置"""

    def add_arguments(self, parser):
        parser.add_argument("--all", dest="_all", action="store_true", help="update all gateway")
        parser.add_argument("--gateway", dest="gateway_name", required=False, help="gateway name")
        parser.add_argument(
            "--hosting-type",
            dest="hosting_type",
            type=int,
            required=True,
            choices=constants.APIHostingTypeEnum.get_values(),
            help="0: apigateway-ng, 1: micro-gateway",
        )
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def handle(self, _all: bool, gateway_name: Optional[str], hosting_type: int, dry_run=False, **kwargs):
        queryset = self._filter_gateway_queryset(_all, gateway_name)
        if not dry_run:
            queryset.exclude(hosting_type=hosting_type).update(hosting_type=hosting_type)

        print("Done")

    def _filter_gateway_queryset(self, _all: bool, gateway_name: Optional[str]):
        if _all:
            return Gateway.objects.all()

        if gateway_name:
            return Gateway.objects.filter(name=gateway_name)

        return Gateway.objects.none()
