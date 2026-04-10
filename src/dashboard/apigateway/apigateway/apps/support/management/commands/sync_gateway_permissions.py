# -*- coding: utf-8 -*-
#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
"""
同步网关权限（含 MCP Server 权限）

输入：gateway_name + 两个资源版本号（version1, version2）

核心逻辑：
1. 根据两个 ResourceVersion 的资源数据，合并生成全量的 resource_name → [resource_id, ...] 映射
2. 查出网关下所有 AppResourcePermission 权限数据
3. 对每条权限记录，通过步骤1的反向映射查出其 resource_id 对应的 resource_name
4. 如果该 resource_name 在全量映射中存在多个 resource_id，
   则为该权限的 bk_app_code 补全所有缺失的 resource_id 权限记录

所有权限操作均为新增（不做删除），支持 --dry-run 模式预览。
"""

import logging
from collections import defaultdict
from typing import Dict, List, Set, Tuple

from django.core.management.base import BaseCommand
from django.db import transaction

from apigateway.apps.permission.models import AppResourcePermission
from apigateway.core.models import Gateway, ResourceVersion

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "同步网关权限（含 MCP Server 权限），基于两个资源版本合并补全 AppResourcePermission"

    def add_arguments(self, parser):
        parser.add_argument(
            "--gateway-name",
            type=str,
            required=True,
            help="网关名称",
        )
        parser.add_argument(
            "--version1",
            type=str,
            required=True,
            help="资源版本号1（如 1.0.0）",
        )
        parser.add_argument(
            "--version2",
            type=str,
            required=True,
            help="资源版本号2（如 2.0.0）",
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            default=False,
            help="dry run 模式，仅输出将要执行的操作，不实际写入数据库",
        )

    def handle(self, *args, **options):
        gateway_name = options["gateway_name"]
        version1 = options["version1"]
        version2 = options["version2"]
        dry_run = options["dry_run"]

        # 查询 Gateway
        gateway = Gateway.objects.filter(name=gateway_name).first()
        if not gateway:
            self.stderr.write(f"Gateway not found: {gateway_name}")
            return

        # 查询两个 ResourceVersion
        rv1 = ResourceVersion.objects.filter(gateway=gateway, version=version1).first()
        if not rv1:
            self.stderr.write(f"ResourceVersion not found: {version1}")
            return

        rv2 = ResourceVersion.objects.filter(gateway=gateway, version=version2).first()
        if not rv2:
            self.stderr.write(f"ResourceVersion not found: {version2}")
            return

        self.stdout.write(f"Gateway: {gateway_name} (id={gateway.id})")
        self.stdout.write(f"Version1: {version1} (id={rv1.id})")
        self.stdout.write(f"Version2: {version2} (id={rv2.id})")
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write("")

        # 构建映射并同步权限
        resource_name_to_ids = self._build_resource_name_to_ids(rv1, rv2)
        resource_id_to_name = self._build_reverse_mapping(resource_name_to_ids)

        self._print_resource_mapping(resource_name_to_ids)
        self._sync_permissions(gateway, resource_name_to_ids, resource_id_to_name, dry_run)

    def _build_resource_name_to_ids(self, rv1: ResourceVersion, rv2: ResourceVersion) -> Dict[str, List[int]]:
        """合并两个 ResourceVersion 的资源数据，生成 resource_name → [resource_id, ...] 映射"""
        resource_name_to_ids: Dict[str, Set[int]] = defaultdict(set)

        for rv in (rv1, rv2):
            for resource in rv.data:
                name = resource.get("name")
                rid = resource.get("id")
                if name and rid:
                    resource_name_to_ids[name].add(rid)

        return {name: sorted(ids) for name, ids in resource_name_to_ids.items()}

    def _build_reverse_mapping(self, resource_name_to_ids: Dict[str, List[int]]) -> Dict[int, str]:
        """构建反向映射：resource_id → resource_name"""
        resource_id_to_name: Dict[int, str] = {}
        for name, ids in resource_name_to_ids.items():
            for rid in ids:
                resource_id_to_name[rid] = name
        return resource_id_to_name

    def _print_resource_mapping(self, resource_name_to_ids: Dict[str, List[int]]):
        """打印资源映射信息"""
        self.stdout.write(f"全量 resource_name 映射（共 {len(resource_name_to_ids)} 个）:")
        for name, ids in sorted(resource_name_to_ids.items()):
            self.stdout.write(f"  {name}: {ids}")

    def _sync_permissions(
        self,
        gateway: Gateway,
        resource_name_to_ids: Dict[str, List[int]],
        resource_id_to_name: Dict[int, str],
        dry_run: bool,
    ):
        """同步权限：对每条权限，补全同 resource_name 下所有 resource_id 的权限记录"""
        # 查出网关下所有 AppResourcePermission（含 expires、grant_type）
        all_permissions = list(
            AppResourcePermission.objects.filter(gateway=gateway).values_list(
                "id", "bk_app_code", "resource_id", "expires", "grant_type"
            )
        )
        self.stdout.write(f"\n网关下 AppResourcePermission 总数: {len(all_permissions)}")

        # 构建 (bk_app_code, resource_id) 已存在集合
        existing_pairs: Set[Tuple[str, int]] = {
            (bk_app_code, resource_id) for _, bk_app_code, resource_id, _, _ in all_permissions
        }

        # 对每条权限，检查是否需要补录
        to_create: List[AppResourcePermission] = []
        seen_to_create: Set[Tuple[str, int]] = set()
        # 按 bk_app_code 汇总补录信息
        app_code_changes: Dict[str, List[str]] = defaultdict(list)

        for _perm_id, bk_app_code, resource_id, expires, grant_type in all_permissions:
            resource_name = resource_id_to_name.get(resource_id)
            if not resource_name:
                continue

            # 该 resource_name 下所有 resource_id
            all_resource_ids = resource_name_to_ids[resource_name]

            for target_resource_id in all_resource_ids:
                if target_resource_id == resource_id:
                    continue

                pair = (bk_app_code, target_resource_id)
                # 已存在于数据库 或 已在待创建列表中，跳过
                if pair in existing_pairs or pair in seen_to_create:
                    continue

                app_code_changes[bk_app_code].append(f"{resource_name}: {resource_id} -> {target_resource_id}")
                to_create.append(
                    AppResourcePermission(
                        bk_app_code=bk_app_code,
                        gateway=gateway,
                        resource_id=target_resource_id,
                        expires=expires,
                        grant_type=grant_type,
                    )
                )
                seen_to_create.add(pair)

        if not to_create:
            self.stdout.write("\n所有权限已完整，无需补录。")
            return

        self._print_changes_summary(app_code_changes, to_create)

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] 以上记录未实际写入数据库。"))
            return

        with transaction.atomic():
            AppResourcePermission.objects.bulk_create(to_create)

        self.stdout.write(self.style.SUCCESS(f"成功补录 {len(to_create)} 条 AppResourcePermission。"))

    def _print_changes_summary(self, app_code_changes: Dict[str, List[str]], to_create: List[AppResourcePermission]):
        """打印补录汇总信息"""
        self.stdout.write(f"\n需要补录 {len(to_create)} 条 AppResourcePermission：")
        for bk_app_code, changes in sorted(app_code_changes.items()):
            self.stdout.write(f"\n  bk_app_code={bk_app_code} ({len(changes)} 条):")
            for change in changes:
                self.stdout.write(f"    {change}")
