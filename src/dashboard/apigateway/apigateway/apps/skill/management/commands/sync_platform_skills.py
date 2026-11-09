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
from collections import Counter
from pathlib import Path

from django.core.management.base import BaseCommand

from apigateway.biz.skill import (
    SKILL_DECLARATIONS_DIR,
    SKILL_RESOURCES_DIR,
    SkillSyncStatusEnum,
    get_changed_metadata_ids,
    sync_platform_skills,
)


class Command(BaseCommand):
    """将内置 Skill 声明同步到数据库"""

    help = "Sync platform skills from declaration files into the database."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dir",
            type=Path,
            default=SKILL_DECLARATIONS_DIR,
            help="Directory of skill declaration YAML files.",
        )
        parser.add_argument(
            "--resources-dir",
            type=Path,
            default=SKILL_RESOURCES_DIR,
            help="Directory of resource snapshot YAML files, one file per gateway.",
        )
        parser.add_argument(
            "--name",
            type=str,
            default="",
            help="Only sync the declaration whose file name (without extension) equals this skill name.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate and render only, do not write to the database.",
        )

    def handle(self, *args, **options):
        declarations_dir: Path = options["dir"]
        if not declarations_dir.is_dir() or not any(declarations_dir.glob("*.yaml")):
            self.stdout.write(f"No skill declarations found in {declarations_dir}, skip.")
            return

        results = sync_platform_skills(
            declarations_dir,
            options["resources_dir"],
            name=options["name"] or None,
            dry_run=options["dry_run"],
        )
        labels = dict(SkillSyncStatusEnum.get_choices())
        for result in results:
            line = f"[{labels[result.status]}] {result.name}"
            if result.reasons:
                line += "：" + "；".join(result.reasons)
            self.stdout.write(self._style(result.status)(line))
            for warning in result.warnings:
                self.stdout.write(self.style.WARNING(f"  warning: {warning}"))

        counts = Counter(result.status for result in results)
        summary = "，".join(f"{labels[status]} {counts[status]}" for status in labels if counts[status])
        prefix = "dry-run " if options["dry_run"] else ""
        self.stdout.write(f"{prefix}total {len(results)}：{summary or '无'}")
        if not options["dry_run"]:
            self.stdout.write(f"changed metadata ids: {get_changed_metadata_ids(results)}")

    def _style(self, status: str):
        if status in (SkillSyncStatusEnum.CREATED.value, SkillSyncStatusEnum.NEW_VERSION.value):
            return self.style.SUCCESS
        if status in (SkillSyncStatusEnum.REJECTED.value, SkillSyncStatusEnum.FAILED.value):
            return self.style.ERROR
        return self.style.WARNING
