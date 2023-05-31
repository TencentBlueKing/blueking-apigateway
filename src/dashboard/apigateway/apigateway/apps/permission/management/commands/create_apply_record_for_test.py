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

from apigateway.apps.permission.constants import ApplyStatusEnum
from apigateway.apps.permission.models import AppPermissionApply
from apigateway.core.models import Resource


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--api-id", type=int, dest="api_id")
        parser.add_argument("--count", type=int, dest="count", default=10, help="record count")
        parser.add_argument("--bk-app-code", dest="bk_app_code", default="apigw-test")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def handle(self, api_id: int, count: int, bk_app_code: str, dry_run: bool, **options) -> None:
        resource_ids = list(Resource.objects.filter(api_id=api_id).values_list("id", flat=True))
        if not resource_ids:
            print(f"warning: api[id={api_id}] has no resources")
            return

        for _ in range(count):
            apply_resource_ids = random.sample(
                resource_ids,
                random.randint(1, min(len(resource_ids), 10)),
            )

            if dry_run:
                print(
                    f"create record: api_id={api_id}, bk_app_code={bk_app_code}, "
                    f"applied_by=admin, resource_ids={apply_resource_ids}"
                )
                continue

            AppPermissionApply.objects.create(
                api_id=api_id,
                bk_app_code=bk_app_code,
                applied_by="admin",
                resource_ids=apply_resource_ids,
                status=ApplyStatusEnum.PENDING.value,
            )
