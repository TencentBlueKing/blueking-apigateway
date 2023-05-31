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
"""迁移 PaaS2/ESB 核心数据至新版 BK-ESB"""
from django.core.management.base import BaseCommand

from apigateway.legacy_esb import sync
from apigateway.legacy_esb.management.commands import pre_check_core_data


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
        parser.add_argument("--force", dest="force", action="store_true", default=False)

    def handle(self, dry_run: bool, force: bool, *args, **options):
        # 预检数据，如果数据不符合预期，将不会继续同步数据
        pre_check_core_data.Command().handle()

        synchronizer_classes = [
            sync.DocCategorySynchronizer,
            sync.ComponentSystemSynchronizer,
            sync.SystemDocCategorySynchronizer,
            sync.ESBChannelSynchronizer,
            sync.ComponentDocSynchronizer,
            sync.AppComponentPermissionSynchronizer,
        ]
        for synchronizer_cls in synchronizer_classes:
            synchronizer_cls().sync_legacy_to_ng(dry_run, force)
