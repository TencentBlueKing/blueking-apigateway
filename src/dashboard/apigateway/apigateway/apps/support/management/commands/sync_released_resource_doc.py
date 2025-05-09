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
将已发布版本的资源文档，同步到 ReleasedResourceDoc
"""

from typing import List

from django.core.management.base import BaseCommand

from apigateway.apps.support.models import ReleasedResourceDoc, ResourceDocVersion
from apigateway.core.models import Gateway, Release


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("--gateway-id", type=int, dest="gateway_id")
        parser.add_argument("--all", dest="_all", action="store_true")
        parser.add_argument("--force", dest="force", action="store_true", help="force")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def handle(self, gateway_id: int, _all: bool, force: bool, dry_run: bool, **options) -> None:
        gateway_ids = self._get_gateway_ids(_all, gateway_id)
        self._sync_released_resource_doc(gateway_ids, force, dry_run)

    def _sync_released_resource_doc(self, gateway_ids: List[int], force: bool, dry_run: bool) -> None:
        resource_version_ids = self._get_released_resource_version_ids(gateway_ids)
        for resource_doc_version in ResourceDocVersion.objects.filter(resource_version_id__in=resource_version_ids):
            exists = ReleasedResourceDoc.objects.filter(
                resource_version_id=resource_doc_version.resource_version_id
            ).exists()
            if exists and not force:
                continue

            if dry_run:
                print(
                    f"sync gateway[id={resource_doc_version.gateway_id}] "
                    f"resource_doc_version[id={resource_doc_version.id}]"
                )
                continue

            ReleasedResourceDoc.objects.save_released_resource_doc(resource_doc_version, force=force)

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
