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
创建权限申请记录，用于测试
"""

import random

from django.core.management.base import BaseCommand

from apigateway.apps.esb.bkcore.models import AppPermissionApplyRecord, ComponentSystem, ESBChannel
from apigateway.apps.permission.constants import ApplyStatusEnum, PermissionApplyExpireDaysEnum


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--system-name", dest="system_name")
        parser.add_argument("--count", type=int, dest="count", default=10, help="record count")
        parser.add_argument("--bk-app-code", dest="bk_app_code", default="apigw-test")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def handle(self, system_name: str, count: int, bk_app_code: str, dry_run: bool, **options) -> None:
        system = ComponentSystem.objects.filter(name=system_name).first()
        if not system:
            print(f"error: system[name={system_name}] not exist")
            return

        component_ids = list(ESBChannel.objects.filter(system_id=system.id).values_list("id", flat=True))
        if not component_ids:
            print(f"warning: system[name={system_name}] has no components")
            return

        for _ in range(count):
            apply_component_ids = random.sample(
                component_ids,
                random.randint(1, min(len(component_ids), 10)),
            )

            if dry_run:
                print(
                    f"create record: system_name={system_name}, bk_app_code={bk_app_code}, "
                    f"applied_by=admin, component_ids={apply_component_ids}"
                )
                continue

            AppPermissionApplyRecord.objects.create(
                bk_app_code=bk_app_code,
                applied_by="admin",
                system=system,
                component_ids=apply_component_ids,
                status=ApplyStatusEnum.PENDING.value,
                expire_days=random.choice(
                    [
                        PermissionApplyExpireDaysEnum.SIX_MONTH.value,
                        PermissionApplyExpireDaysEnum.TWELVE_MONTH.value,
                    ]
                ),
            )
