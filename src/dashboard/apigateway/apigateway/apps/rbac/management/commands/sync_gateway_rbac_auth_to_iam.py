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
import time
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apigateway.apps.rbac.iam_context import GatewayIAMSyncContext
from apigateway.biz.iam import BK_IAM_V4_SYSTEM_ID, GatewayIAMAuthorizationSynchronizer, GatewayIAMSyncResult
from apigateway.core.models import Gateway

DEFAULT_GATEWAY_DELAY_SECONDS = 0.05
GATEWAY_ID_ITERATOR_CHUNK_SIZE = 1000
MAX_LOGGED_CHANGES = 20


@dataclass
class _RunSummary:
    gateways: int
    succeeded: int = 0
    with_warnings: int = 0
    unchanged_gateways: int = 0
    failed: int = 0
    grants_planned: int = 0
    grants_succeeded: int = 0
    grants_skipped_missing: int = 0
    grants_skipped_excluded: int = 0
    grants_retry_failed: int = 0
    revokes_planned: int = 0
    revokes_succeeded: int = 0
    revokes_skipped_excluded: int = 0
    unchanged: int = 0

    @property
    def needs_retry(self) -> bool:
        return bool(self.grants_skipped_missing or self.grants_retry_failed)


class Command(BaseCommand):
    help = "以本地 GatewayMember 为准，对账权限中心 V4 网关角色授权"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--gateway", help="仅对账指定网关 ID 或名称")
        parser.add_argument("--username", help="对所有现存网关仅对账指定用户")
        parser.add_argument("--all", action="store_true", help="对账全部现存网关")
        mode = parser.add_mutually_exclusive_group()
        mode.add_argument("--apply", action="store_true", help="查询差异并立即应用变更")
        mode.add_argument("--dry-run", action="store_true", help="仅查询并输出计划，不修改 IAM；默认模式")
        parser.add_argument(
            "--initial",
            action="store_true",
            help="首次部署全量同步；已成功执行过则跳过，仅可与 --all --apply 配合",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=100,
            help="查询单个 IAM 角色授权时的分页大小",
        )
        parser.add_argument(
            "--gateway-delay",
            type=float,
            default=DEFAULT_GATEWAY_DELAY_SECONDS,
            help=f"处理相邻网关之间的限速等待秒数，默认 {DEFAULT_GATEWAY_DELAY_SECONDS}",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        run_id = uuid.uuid4().hex[:12]
        if not settings.BK_IAM_V4_ENABLED:
            self.stdout.write(f"event=iam-rbac-sync-summary run_id={run_id} status=skipped reason=iam-disabled")
            return

        self._validate_arguments(options)
        initial_sync_context = GatewayIAMSyncContext()
        if options["initial"] and initial_sync_context.is_initial_sync_completed():
            self.stdout.write(
                f"event=iam-rbac-sync-summary run_id={run_id} mode=apply status=skipped "
                "reason=initial-sync-already-completed"
            )
            return

        try:
            gateway_ids = self._get_gateway_ids(options)
            mode = "apply" if options["apply"] else "dry-run"
            started_at = time.monotonic()
            username_filter = options["username"] or "all"
            self.stdout.write(
                f"event=iam-rbac-sync-start run_id={run_id} mode={mode} gateways_total={len(gateway_ids)} "
                f"username_filter={username_filter} page_size={options['page_size']}"
            )
            summary = self._reconcile_gateways(
                gateway_ids,
                apply=options["apply"],
                operator=BK_IAM_V4_SYSTEM_ID,
                username=options["username"],
                page_size=options["page_size"],
                gateway_delay=options["gateway_delay"],
                mode=mode,
                run_id=run_id,
            )
            self._write_summary(
                summary,
                mode=mode,
                run_id=run_id,
                duration_ms=int((time.monotonic() - started_at) * 1000),
            )
            self._raise_for_failures(summary, run_id=run_id)
            if options["initial"]:
                if summary.needs_retry:
                    self.stdout.write(
                        f"event=iam-rbac-initial-sync run_id={run_id} mode=apply status=incomplete "
                        "reason=incomplete-authorizations 首次同步存在未完成授权，未记录完成标记，下次部署将重试"
                    )
                else:
                    initial_sync_context.mark_initial_sync_completed()
                    self.stdout.write(f"event=iam-rbac-initial-sync run_id={run_id} mode=apply status=completed")
        except Exception as err:
            if isinstance(err, CommandError):
                raise
            raise CommandError(f"网关 RBAC 权限对账失败: {err}") from err

    def _validate_arguments(self, options: dict[str, Any]) -> None:
        selectors = [
            bool(options["gateway"]),
            bool(options["username"]),
            bool(options["all"]),
        ]
        if sum(selectors) != 1:
            raise CommandError("必须且只能指定 --gateway、--username、--all 之一")
        if options["apply"] and options["dry_run"]:
            raise CommandError("--apply 与 --dry-run 不能同时指定")
        if options["initial"] and not (options["all"] and options["apply"]):
            raise CommandError("--initial 必须与 --all --apply 配合使用")

        if not 1 <= options["page_size"] <= 100:
            raise CommandError("--page-size 必须在 1 到 100 之间")
        if options["gateway_delay"] < 0:
            raise CommandError("--gateway-delay 不能小于 0")
        if options["username"] is not None and not options["username"].strip():
            raise CommandError("--username 不能为空")

    def _get_gateway_ids(self, options: dict[str, Any]) -> list[int]:
        gateway_selector = options["gateway"]
        if gateway_selector is None:
            return list(
                Gateway.objects.order_by("id")
                .values_list("id", flat=True)
                .iterator(chunk_size=GATEWAY_ID_ITERATOR_CHUNK_SIZE)
            )

        gateway_id = None
        try:
            parsed_gateway_id = int(gateway_selector)
        except TypeError, ValueError:
            pass
        else:
            gateway_id = Gateway.objects.filter(id=parsed_gateway_id).values_list("id", flat=True).first()
        if gateway_id is None:
            gateway_id = Gateway.objects.filter(name=gateway_selector).values_list("id", flat=True).first()
        if gateway_id is None:
            raise CommandError(f"网关不存在: {gateway_selector}")
        return [gateway_id]

    def _reconcile_gateways(
        self,
        gateway_ids: list[int],
        *,
        apply: bool,
        operator: str,
        username: str | None,
        page_size: int,
        gateway_delay: float,
        mode: str,
        run_id: str,
    ) -> _RunSummary:
        synchronizer = GatewayIAMAuthorizationSynchronizer(page_size=page_size)
        gateway_names = dict(Gateway.objects.filter(id__in=gateway_ids).values_list("id", "name"))
        total = len(gateway_ids)
        summary = _RunSummary(gateways=total)

        for index, gateway_id in enumerate(gateway_ids, start=1):
            gateway_started_at = time.monotonic()
            try:
                result = synchronizer.reconcile_gateway(
                    gateway_id,
                    apply=apply,
                    operator=operator,
                    username=username,
                )
            except Exception as err:
                gateway_name = gateway_names.get(gateway_id, "unknown")
                summary.failed += 1
                self.stderr.write(
                    f"event=iam-rbac-sync-gateway run_id={run_id} mode={mode} "
                    f"gateway_index={index} gateways_total={total} "
                    f"status=failed gateway_id={gateway_id} gateway_name={gateway_name} "
                    f"write_result={'unknown' if apply else 'not-applicable'} "
                    f"error={json.dumps(str(err), ensure_ascii=False)} "
                    f"duration_ms={int((time.monotonic() - gateway_started_at) * 1000)}"
                )
                if gateway_delay and index < total:
                    time.sleep(gateway_delay)
                continue

            if result.has_warnings:
                summary.with_warnings += 1
            elif not result.change_count:
                summary.unchanged_gateways += 1
            else:
                summary.succeeded += 1
            summary.grants_planned += result.grant_count
            summary.revokes_planned += result.revoke_count
            summary.unchanged += result.unchanged
            summary.grants_succeeded += result.grant_write_result.succeeded
            summary.grants_skipped_missing += result.grant_write_result.skipped_missing
            summary.grants_skipped_excluded += result.grant_write_result.skipped_excluded
            summary.grants_retry_failed += result.grant_write_result.failed
            summary.revokes_succeeded += result.revoke_write_result.succeeded
            summary.revokes_skipped_excluded += result.revoke_write_result.skipped_excluded
            change_count = result.change_count
            changes, changes_logged = self._format_changes(result)
            write_counts = ""
            if apply:
                write_counts = (
                    f"grants_succeeded={result.grant_write_result.succeeded} "
                    f"grants_skipped_missing={result.grant_write_result.skipped_missing} "
                    f"grants_skipped_excluded={result.grant_write_result.skipped_excluded} "
                    f"grants_retry_failed={result.grant_write_result.failed} "
                    f"revokes_succeeded={result.revoke_write_result.succeeded} "
                    f"revokes_skipped_excluded={result.revoke_write_result.skipped_excluded} "
                )
            outcome = "changed" if change_count else "no-change"
            if not apply and change_count:
                outcome = "planned"
            elif result.has_warnings:
                outcome = (
                    "partial"
                    if result.grant_write_result.succeeded or result.revoke_write_result.succeeded
                    else "skipped"
                )
                if result.grant_write_result.failed:
                    outcome = "incomplete"
            self.stdout.write(
                f"event=iam-rbac-sync-gateway run_id={run_id} mode={mode} "
                f"gateway_index={index} gateways_total={total} "
                f"status={'completed-with-warnings' if result.has_warnings else 'success'} outcome={outcome} "
                f"gateway_id={result.gateway_id} gateway_name={result.gateway_name} "
                f"grants_planned={result.grant_count} revokes_planned={result.revoke_count} "
                f"{write_counts}already_consistent={result.unchanged} changes_scope=planned "
                f"changes={json.dumps(changes, ensure_ascii=False)} "
                f"changes_logged={changes_logged} changes_omitted={change_count - changes_logged} "
                f"duration_ms={int((time.monotonic() - gateway_started_at) * 1000)}"
            )
            if gateway_delay and index < total:
                time.sleep(gateway_delay)
        return summary

    @staticmethod
    def _format_changes(result: GatewayIAMSyncResult) -> tuple[str, int]:
        items = [("grant", item) for item in result.grants]
        items.extend(("revoke", item) for item in result.revokes)
        logged_items = items[:MAX_LOGGED_CHANGES]
        changes = ";".join(
            f"{operation}(username={item.username},role={item.role},reason={item.reason},"
            f"expires_at={datetime.fromtimestamp(item.expired_at, tz=UTC).isoformat().replace('+00:00', 'Z')})"
            for operation, item in logged_items
        )
        return changes, len(logged_items)

    def _write_summary(self, summary: _RunSummary, *, mode: str, run_id: str, duration_ms: int) -> None:
        failure_count = summary.failed
        if failure_count:
            status = "failed" if failure_count == summary.gateways else "partial-failure"
        else:
            status = "completed-with-warnings" if summary.with_warnings else "success"
        write_counts = ""
        if mode == "apply":
            write_counts = (
                f"grants_succeeded={summary.grants_succeeded} "
                f"grants_skipped_missing={summary.grants_skipped_missing} "
                f"grants_skipped_excluded={summary.grants_skipped_excluded} "
                f"grants_retry_failed={summary.grants_retry_failed} "
                f"revokes_succeeded={summary.revokes_succeeded} "
                f"revokes_skipped_excluded={summary.revokes_skipped_excluded} "
            )
        self.stdout.write(
            f"event=iam-rbac-sync-summary run_id={run_id} mode={mode} status={status} "
            f"gateways_total={summary.gateways} gateways_succeeded={summary.succeeded} "
            f"gateways_with_warnings={summary.with_warnings} gateways_unchanged={summary.unchanged_gateways} "
            f"gateways_failed={failure_count} grants_planned={summary.grants_planned} "
            f"revokes_planned={summary.revokes_planned} {write_counts}already_consistent={summary.unchanged} "
            f"failed_gateway_changes={'none' if failure_count == 0 else 'unknown'} duration_ms={duration_ms}"
        )
        self.stdout.write(
            f"网关 RBAC 权限对账{'预览' if mode == 'dry-run' else '完成'}："
            f"网关共 {summary.gateways} 个，{'计划变更' if mode == 'dry-run' else '成功'} {summary.succeeded} 个，"
            f"有警告 {summary.with_warnings} 个，无需变更 {summary.unchanged_gateways} 个，失败 {summary.failed} 个；"
            + (
                f"授权项计划新增/更新 {summary.grants_planned} 项，撤销 {summary.revokes_planned} 项"
                if mode == "dry-run"
                else f"授权项成功 {summary.grants_succeeded} 项，用户不存在跳过 {summary.grants_skipped_missing} 项，"
                f"配置排除跳过 {summary.grants_skipped_excluded} 项，重试失败（未确认写入）{summary.grants_retry_failed} 项；"
                f"撤权成功 {summary.revokes_succeeded} 项，配置排除跳过 {summary.revokes_skipped_excluded} 项"
            )
            + ("；异常失败网关的写入结果未知，不计入上述授权项统计" if failure_count else "")
            + f"；run_id={run_id}"
        )

    def _raise_for_failures(self, summary: _RunSummary, *, run_id: str) -> None:
        if not summary.failed:
            return
        raise CommandError(
            f"网关 RBAC 权限对账失败: {summary.failed}/{summary.gateways} 个网关失败; "
            f"run_id={run_id}; 请检索 event=iam-rbac-sync-gateway status=failed"
        )
