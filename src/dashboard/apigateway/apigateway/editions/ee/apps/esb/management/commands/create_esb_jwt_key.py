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
创建 esb JWT 密钥
"""
import logging

from django.core.management.base import BaseCommand

from apigateway.apps.esb.bkcore.models import FunctionController
from apigateway.utils.crypto import KeyGenerator

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)

    def handle(self, dry_run: bool, *args, **options):
        if FunctionController.objects.get_jwt_key():
            logger.info("esb jwt key already exists, skip")
            return

        if not dry_run:
            private_key, public_key = KeyGenerator().generate_rsa_key()
            FunctionController.objects.save_jwt_key(private_key, public_key)

        logger.info("create esb jwt key")
