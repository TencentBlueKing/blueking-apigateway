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
import logging

from django.core.management.base import BaseCommand, CommandParser
from pydantic import BaseModel, Field

from apigateway.apps.mcp_server.models import MCPServerAppPermissionApply
from apigateway.apps.permission.models import AppPermissionRecord
from apigateway.apps.permission.tasks import (
    async_fill_gateway_or_resource_itsm_approver,
    async_fill_mcp_server_itsm_approver,
)

logger = logging.getLogger(__name__)

TYPE_GATEWAY = "gateway"
TYPE_MCP = "mcp"
TYPE_ALL = "all"
# Keep aligned with apigateway.biz.bk_itsm.bk_itsm.ITSM_PERMISSION_APPROVAL_HANDLER
ITSM_HANDLED_BY_PLACEHOLDER = "itsm"


class BackfillStats(BaseModel):
    total: int = Field(default=0)
    success: int = Field(default=0)
    failed: int = Field(default=0)


class Command(BaseCommand):
    help = (
        "Synchronously backfill actual ITSM approvers for historical records. "
        "Gateway/resource uses AppPermissionRecord (--record-id); "
        "MCP server uses MCPServerAppPermissionApply (--mcp-apply-id)."
    )

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("--dry-run", action="store_true", help="Preview candidates without backfilling")
        parser.add_argument(
            "--force",
            action="store_true",
            help=f'Include records whose handled_by is not "{ITSM_HANDLED_BY_PLACEHOLDER}"',
        )
        parser.add_argument(
            "--type",
            dest="record_type",
            choices=[TYPE_ALL, TYPE_GATEWAY, TYPE_MCP],
            default=TYPE_ALL,
            help="Which records to scan: gateway=AppPermissionRecord, mcp=MCPServerAppPermissionApply",
        )
        parser.add_argument("--limit", type=int, default=0, help="Max records to process per type; 0 means no limit")
        parser.add_argument(
            "--record-id",
            type=int,
            help="Only process one gateway/resource AppPermissionRecord id",
        )
        parser.add_argument(
            "--mcp-apply-id",
            type=int,
            help="Only process one MCPServerAppPermissionApply id",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        force = options["force"]
        record_type = options["record_type"]
        limit = options["limit"]
        record_id = options.get("record_id")
        mcp_apply_id = options.get("mcp_apply_id")

        gateway_stats = BackfillStats()
        mcp_stats = BackfillStats()

        if record_type in (TYPE_ALL, TYPE_GATEWAY) and mcp_apply_id is None:
            gateway_stats = self._backfill_gateway_or_resource(
                dry_run=dry_run,
                force=force,
                limit=limit,
                record_id=record_id,
            )

        if record_type in (TYPE_ALL, TYPE_MCP) and record_id is None:
            mcp_stats = self._backfill_mcp(
                dry_run=dry_run,
                force=force,
                limit=limit,
                mcp_apply_id=mcp_apply_id,
            )

        mode = "dry-run" if dry_run else "backfill"
        self.stdout.write(
            f"mode={mode} "
            f"gateway_total={gateway_stats.total} gateway_success={gateway_stats.success} "
            f"gateway_failed={gateway_stats.failed} "
            f"mcp_total={mcp_stats.total} mcp_success={mcp_stats.success} mcp_failed={mcp_stats.failed}"
        )

    def _build_queryset(self, model, force: bool, pk: int | None):
        qs = model.objects.exclude(itsm_ticket_id="")
        if pk is not None:
            qs = qs.filter(id=pk)
        elif not force:
            qs = qs.filter(handled_by=ITSM_HANDLED_BY_PLACEHOLDER)
        return qs.order_by("id")

    @staticmethod
    def _is_backfilled(handled_by: str) -> bool:
        return bool(handled_by) and handled_by != ITSM_HANDLED_BY_PLACEHOLDER

    def _backfill_gateway_or_resource(
        self, dry_run: bool, force: bool, limit: int, record_id: int | None
    ) -> BackfillStats:
        qs = self._build_queryset(AppPermissionRecord, force=force, pk=record_id)
        stats = BackfillStats()

        for record in qs.iterator():
            if limit > 0 and stats.total >= limit:
                break
            stats.total += 1
            self.stdout.write(
                f"gateway record_id={record.id} grant_dimension={record.grant_dimension} "
                f"ticket_id={record.itsm_ticket_id} handled_by={record.handled_by}"
            )
            if dry_run:
                continue
            try:
                # Call the shared task body synchronously; no Celery worker required.
                async_fill_gateway_or_resource_itsm_approver(
                    record.grant_dimension,
                    record.id,
                    record.itsm_ticket_id,
                )
            except Exception as err:  # pylint: disable=broad-except
                stats.failed += 1
                logger.exception(
                    "backfill gateway itsm approver failed, record_id=%s, ticket_id=%s",
                    record.id,
                    record.itsm_ticket_id,
                )
                self.stderr.write(
                    self.style.ERROR(
                        f"gateway backfill failed record_id={record.id} ticket_id={record.itsm_ticket_id} err={err}"
                    )
                )
                continue

            record.refresh_from_db()
            if self._is_backfilled(record.handled_by):
                stats.success += 1
                self.stdout.write(f"gateway record_id={record.id} handled_by={record.handled_by}")
            else:
                stats.failed += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"gateway backfill failed record_id={record.id} ticket_id={record.itsm_ticket_id} "
                        "approver empty"
                    )
                )
        return stats

    def _backfill_mcp(self, dry_run: bool, force: bool, limit: int, mcp_apply_id: int | None) -> BackfillStats:
        qs = self._build_queryset(MCPServerAppPermissionApply, force=force, pk=mcp_apply_id)
        stats = BackfillStats()

        for apply_obj in qs.iterator():
            if limit > 0 and stats.total >= limit:
                break
            stats.total += 1
            self.stdout.write(
                f"mcp apply_id={apply_obj.id} ticket_id={apply_obj.itsm_ticket_id} handled_by={apply_obj.handled_by}"
            )
            if dry_run:
                continue
            try:
                async_fill_mcp_server_itsm_approver(apply_obj.id, apply_obj.itsm_ticket_id)
            except Exception as err:  # pylint: disable=broad-except
                stats.failed += 1
                logger.exception(
                    "backfill mcp itsm approver failed, apply_id=%s, ticket_id=%s",
                    apply_obj.id,
                    apply_obj.itsm_ticket_id,
                )
                self.stderr.write(
                    self.style.ERROR(
                        f"mcp backfill failed apply_id={apply_obj.id} ticket_id={apply_obj.itsm_ticket_id} err={err}"
                    )
                )
                continue

            apply_obj.refresh_from_db()
            if self._is_backfilled(apply_obj.handled_by):
                stats.success += 1
                self.stdout.write(f"mcp apply_id={apply_obj.id} handled_by={apply_obj.handled_by}")
            else:
                stats.failed += 1
                self.stderr.write(
                    self.style.ERROR(
                        f"mcp backfill failed apply_id={apply_obj.id} ticket_id={apply_obj.itsm_ticket_id} "
                        "approver empty"
                    )
                )
        return stats
