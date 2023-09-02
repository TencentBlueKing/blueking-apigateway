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

from django.core.management.base import BaseCommand, CommandError

from apigateway.core.models import APIRelatedApp, Gateway
from apigateway.utils.django import get_object_or_None

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """添加网关绑定到应用"""

    def add_arguments(self, parser):
        parser.add_argument("--gateway-name", type=str, dest="gateway_name", required=True)
        parser.add_argument("--app-code", type=str, dest="bk_app_code", required=True)

    def handle(self, gateway_name: str, bk_app_code: str, **options):
        gateway = get_object_or_None(Gateway, name=gateway_name)
        if not gateway:
            raise CommandError(f"gateway not found: gateway_name={gateway_name}")

        APIRelatedApp.objects.add_related_app(gateway.id, bk_app_code)

        logger.info(f"add related app success: gateway_name={gateway_name}, app_code={bk_app_code}")
