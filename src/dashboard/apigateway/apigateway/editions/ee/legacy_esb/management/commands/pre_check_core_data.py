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
"""检查 PaaS2/ESB 中的数据，是否满足迁移条件，如果不满足，则无法直接迁移"""
import logging
import sys

from django.core.management.base import BaseCommand

from apigateway.legacy_esb import models as legacy_models
from apigateway.legacy_esb import sync

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def handle(self, *args, **options):
        self.check_legacy_doc_category()
        self.check_field_values()

        logger.info("check ok")

    def check_legacy_doc_category(self):
        duplicate_names = legacy_models.SystemDocCategory.objects.get_duplicate_names()
        if duplicate_names:
            logger.error(
                f"旧版文档分类中，name={', '.join(duplicate_names)} 重复，请手动删除重复数据，或调用 `python manage.py fix_legacy_data` 删除重复数据"
            )
            sys.exit(1)

    def check_field_values(self):
        pre_check_synchronizeres = [
            sync.DocCategorySynchronizer(),
            sync.ComponentSystemSynchronizer(),
            sync.ESBChannelSynchronizer(),
            sync.AppComponentPermissionSynchronizer(),
        ]
        for synchronizer in pre_check_synchronizeres:
            result, message = synchronizer.pre_check_data()
            if not result:
                logger.error(message)
                logger.error("新版与旧版核心数据有差异，需调用指令 `python manage.py clear_ng_core_data` 删除新版数据后，再同步")
                sys.exit(1)
