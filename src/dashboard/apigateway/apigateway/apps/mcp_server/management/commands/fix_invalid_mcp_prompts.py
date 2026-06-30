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
import json
from typing import List

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apigateway.apps.mcp_server.constants import MCPServerExtendTypeEnum
from apigateway.apps.mcp_server.models import MCPServerExtend


def _parse_mcp_server_ids(value: str) -> List[int]:
    ids: List[int] = []
    for raw_item in value.split(","):
        mcp_server_id_str = raw_item.strip()
        if not mcp_server_id_str:
            continue
        try:
            ids.append(int(mcp_server_id_str))
        except ValueError as err:
            raise CommandError(f"Invalid mcp_server_id: {mcp_server_id_str}") from err

    if not ids:
        raise CommandError("No valid mcp_server_ids provided.")

    return ids


def _validate_prompts_payload(prompts):
    if not isinstance(prompts, list):
        raise TypeError("prompts must be a list")

    for prompt in prompts:
        if not isinstance(prompt, dict):
            raise TypeError("prompt item must be a dict")


class Command(BaseCommand):
    help = """
    Check or fix invalid MCP prompts JSON content.

    Examples:
      python manage.py fix_invalid_mcp_prompts --dry-run
      python manage.py fix_invalid_mcp_prompts --apply
      python manage.py fix_invalid_mcp_prompts --dry-run --mcp-server-ids 396,397
      python manage.py fix_invalid_mcp_prompts --apply --mcp-server-ids 396,397
    """

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            default=False,
            help="Only list invalid records, do not modify data.",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            default=False,
            help="Fix invalid records by replacing prompts content with []",
        )
        parser.add_argument(
            "--mcp-server-ids",
            type=str,
            default="",
            help="Only process specified mcp_server_ids, comma separated, e.g. 396,397",
        )
        parser.add_argument(
            "--updated-by",
            type=str,
            default="system",
            help="updated_by when applying fix, default is system",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        apply_fix = options["apply"]
        mcp_server_ids_raw = options.get("mcp_server_ids", "")
        updated_by = options["updated_by"]

        if dry_run and apply_fix:
            raise CommandError("Only one of --dry-run or --apply can be specified.")

        if not dry_run and not apply_fix:
            dry_run = True

        queryset = MCPServerExtend.objects.filter(
            type=MCPServerExtendTypeEnum.PROMPTS.value,
        ).exclude(content="")

        if mcp_server_ids_raw:
            mcp_server_ids = _parse_mcp_server_ids(mcp_server_ids_raw)
            queryset = queryset.filter(mcp_server_id__in=mcp_server_ids)

        total = queryset.count()
        invalid_extends: List[MCPServerExtend] = []

        self.stdout.write(f"Scanning prompts content, total records={total}")

        for extend in queryset.iterator(chunk_size=200):
            try:
                prompts = json.loads(extend.content)
                _validate_prompts_payload(prompts)
            except json.JSONDecodeError as err:
                invalid_extends.append(extend)
                self.stdout.write(
                    self.style.ERROR(
                        "Invalid prompts JSON/payload: "
                        f"mcp_server_id={extend.mcp_server_id}, extend_id={extend.id}, error={err.msg}"
                    )
                )
            except TypeError as err:
                invalid_extends.append(extend)
                self.stdout.write(
                    self.style.ERROR(
                        "Invalid prompts JSON/payload: "
                        f"mcp_server_id={extend.mcp_server_id}, extend_id={extend.id}, error={err}"
                    )
                )

        invalid_count = len(invalid_extends)
        if invalid_count == 0:
            self.stdout.write(self.style.SUCCESS("No invalid prompts JSON/payload found."))
            return

        self.stdout.write(self.style.WARNING(f"Found invalid prompts JSON records: {invalid_count}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS("Dry run mode: no data changed."))
            return

        now = timezone.now()
        for extend in invalid_extends:
            extend.content = "[]"
            extend.updated_by = updated_by
            extend.updated_time = now
            extend.save(update_fields=["content", "updated_by", "updated_time"])

        self.stdout.write(self.style.SUCCESS(f"Apply mode: fixed records={invalid_count}"))
