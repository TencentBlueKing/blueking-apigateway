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
"""删除新版 BK-ESB 中的部分核心数据，防止迁移旧版 PaaS2/ESB 时数据冲突"""

import logging

from django.core.management.base import BaseCommand

from apigateway.apps.esb.bkcore.models import (
    AppComponentPermission,
    AppPermissionApplyRecord,
    ComponentDoc,
    ComponentResourceBinding,
    ComponentSystem,
    DocCategory,
    ESBChannel,
    SystemDocCategory,
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)

    def handle(self, dry_run: bool, *args, **options):
        self._clear_ng_core_data(dry_run)

    def _clear_ng_core_data(self, dry_run: bool):
        if dry_run:
            logger.info("delete all system doc-category relations")
            logger.info("delete all doc-categories")
            logger.info("delete all component-docs")
            logger.info("delete all app-component-permissions")
            logger.info("delete all component-resource-binding")
            logger.info("delete all components")
            logger.info("delete all systems")
            return

        if self._is_confirmed_clear_ng_core_data():
            self._delete_ng_core_data()
            logger.info("clear ng core data done")

    def _delete_ng_core_data(self):
        SystemDocCategory.objects.all().delete()
        DocCategory.objects.all().delete()
        ComponentDoc.objects.all().delete()
        AppComponentPermission.objects.all().delete()
        ComponentResourceBinding.objects.all().delete()
        AppPermissionApplyRecord.objects.all().delete()
        ESBChannel.objects.all().delete()
        ComponentSystem.objects.all().delete()

    def _is_confirmed_clear_ng_core_data(self) -> bool:
        tips = "{}\n确认是否删除新版中以上模型的所有数据，可能导致新版组件 API 无法访问，请谨慎操作".format(
            "\n".join(
                [
                    "ComponentSystem",
                    "DocCategory",
                    "SystemDocCategory",
                    "ESBChannel",
                    "ComponentDoc",
                    "AppComponentPermission",
                    "AppPermissionApplyRecord",
                    "ComponentResourceBinding",
                ]
            )
        )
        confirm = input(f"{tips}：yes/no?")
        return confirm == "yes"
