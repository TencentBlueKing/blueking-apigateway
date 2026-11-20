# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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
将已发布版本的资源信息，同步到 ReleasedResource
"""

from typing import List

from django.core.management.base import BaseCommand

from apigateway.core.managers import RELEASED_RESOURCE_CREATE_BATCH_SIZE, get_released_resource_oauth2_app_flags
from apigateway.core.models import Gateway, Release, ReleasedResource, ResourceVersion


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--gateway-id", type=int, dest="gateway_id")
        parser.add_argument("--all", dest="_all", action="store_true")
        parser.add_argument("--force", dest="force", action="store_true", help="force")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")
        parser.add_argument(
            "--oauth2-app-flags",
            dest="oauth2_app_flags",
            action="store_true",
            help=(
                "recompute oauth2_app_delegated_enabled/oauth2_app_only_enabled of existing rows from their "
                "resource snapshot in place, and create missing rows; repeatable, no delete"
            ),
        )

    def handle(
        self, gateway_id: int, _all: bool, force: bool, dry_run: bool, oauth2_app_flags: bool = False, **options
    ) -> None:
        gateway_ids = self._get_gateway_ids(_all, gateway_id)
        if oauth2_app_flags:
            self._refresh_oauth2_app_flags(gateway_ids, dry_run)
            return
        self._sync_released_resource(gateway_ids, force, dry_run)

    def _refresh_oauth2_app_flags(self, gateway_ids: List[int], dry_run: bool) -> None:
        total = 0
        for resource_version in ResourceVersion.objects.filter(
            id__in=self._get_released_resource_version_ids(gateway_ids)
        ).only("id", "gateway_id"):
            if not ReleasedResource.objects.filter(resource_version_id=resource_version.id).exists():
                self.stdout.write(
                    f"create gateway[id={resource_version.gateway_id}] resource_version[id={resource_version.id}]"
                )
                if not dry_run:
                    # only() 未加载 data，保存投影时需要完整版本
                    ReleasedResource.objects.save_released_resource(
                        ResourceVersion.objects.get(id=resource_version.id)
                    )
                continue

            count = self._refresh_resource_version_flags(resource_version.id, dry_run)
            if count:
                total += count
                self.stdout.write(
                    f"refresh gateway[id={resource_version.gateway_id}] "
                    f"resource_version[id={resource_version.id}] rows={count}"
                )

        self.stdout.write(f"{'would refresh' if dry_run else 'refreshed'} {total} rows")

    @staticmethod
    def _refresh_resource_version_flags(resource_version_id: int, dry_run: bool) -> int:
        """按每行资源快照重新推导应用通道投影列，只更新与推导结果不一致的行，可重复执行

        旧版 Dashboard 写入的行没有这两列，取数据库默认值 false；再次升级后用于补算
        """
        to_update = []
        queryset = ReleasedResource.objects.filter(resource_version_id=resource_version_id).only(
            "id", "data", "oauth2_app_delegated_enabled", "oauth2_app_only_enabled"
        )
        for released_resource in queryset.iterator(chunk_size=RELEASED_RESOURCE_CREATE_BATCH_SIZE):
            delegated_enabled, app_only_enabled = get_released_resource_oauth2_app_flags(released_resource.data)
            if (
                released_resource.oauth2_app_delegated_enabled == delegated_enabled
                and released_resource.oauth2_app_only_enabled == app_only_enabled
            ):
                continue
            released_resource.oauth2_app_delegated_enabled = delegated_enabled
            released_resource.oauth2_app_only_enabled = app_only_enabled
            to_update.append(released_resource)

        if to_update and not dry_run:
            ReleasedResource.objects.bulk_update(
                to_update,
                ["oauth2_app_delegated_enabled", "oauth2_app_only_enabled"],
                batch_size=RELEASED_RESOURCE_CREATE_BATCH_SIZE,
            )
        return len(to_update)

    def _sync_released_resource(self, gateway_ids: List[int], force: bool, dry_run: bool) -> None:
        resource_version_ids = self._get_released_resource_version_ids(gateway_ids)
        for resource_version in ResourceVersion.objects.filter(id__in=resource_version_ids):
            exists = ReleasedResource.objects.filter(resource_version_id=resource_version.id).exists()
            if exists and not force:
                continue

            if dry_run:
                print(f"sync gateway[id={resource_version.gateway_id}] resource_version[id={resource_version.id}]")
                continue

            ReleasedResource.objects.save_released_resource(resource_version, force=force)

    def _get_gateway_ids(self, _all: bool, gateway_id: int) -> List[int]:
        if _all:
            return list(Gateway.objects.all().values_list("id", flat=True))

        if gateway_id:
            return list(Gateway.objects.filter(id=gateway_id).values_list("id", flat=True))

        return []

    def _get_released_resource_version_ids(self, gateway_ids: List[int]) -> List[int]:
        return list(
            Release.objects.filter(gateway_id__in=gateway_ids)
            .order_by("resource_version_id")
            .distinct()
            .values_list("resource_version_id", flat=True)
        )
