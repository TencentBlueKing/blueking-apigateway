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
"""PaaS2/ESB 核心数据迁移完成后，校验迁移前后数据是否一致"""
from django.core.management.base import BaseCommand

from apigateway.legacy_esb import sync


class Command(BaseCommand):
    def handle(self, *args, **options):
        synchronizer_classes = [
            sync.DocCategorySynchronizer,
            sync.ComponentSystemSynchronizer,
            sync.SystemDocCategorySynchronizer,
            sync.ESBChannelSynchronizer,
            sync.ComponentDocSynchronizer,
            sync.AppComponentPermissionSynchronizer,
        ]
        for synchronizer_cls in synchronizer_classes:
            synchronizer_cls().assert_data()
