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
"""检查 PaaS2/ESB 自助接入组件配置是否满足迁移需求"""

import logging
import re
import sys
from collections import defaultdict

from django.core.management.base import BaseCommand

from apigateway.legacy_esb import models as legacy_models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.check_extra_headers()

        logger.info("check ok")

    def check_extra_headers(self):
        usable_header_key_pattern = re.compile(r"^[a-zA-Z0-9-_]{1,100}$")
        id_to_invalid_header_keys = defaultdict(list)
        id_to_underscore_header_keys = defaultdict(list)

        buffet_components = legacy_models.ESBBuffetComponent.objects.all()
        for component in buffet_components:
            for key in component.extra_headers_dict:
                if not usable_header_key_pattern.match(key):
                    id_to_invalid_header_keys[component.id].append(key)
                    continue

                if "_" in key:
                    id_to_underscore_header_keys[component.id].append(key)

        if id_to_invalid_header_keys:
            logger.error(
                "以下自助接入组件的 extra_headers 中包含不符合规则的请求头，请修复后再迁移\n%s",
                "\n".join(
                    [
                        f"id={id_}, invalid_header_keys: {', '.join(header_keys)}"
                        for id_, header_keys in id_to_invalid_header_keys.items()
                    ]
                ),
            )
            sys.exit(1)

        if id_to_underscore_header_keys:
            logger.error(
                "以下自助接入组件的 extra_headers 中存在包含下划线(_)的请求头，迁移时，会将下划线自动转换为中折线(-)，迁移前请确认可否默认转换\n%s",
                "\n".join(
                    [
                        f"id={id_}, invalid_header_keys: {', '.join(header_keys)}"
                        for id_, header_keys in id_to_underscore_header_keys.items()
                    ]
                ),
            )
            sys.exit(1)
