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
from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apigateway.apps.rbac.iam_context import GatewayIAMSyncContext
from apigateway.biz.iam import GatewayIAMAuthorizationSynchronizer, get_gateway_iam_system_operator
from apigateway.core.models import Gateway

DEFAULT_MAX_CHANGES = 1000
DEFAULT_GATEWAY_DELAY_SECONDS = 0.05
GATEWAY_ID_ITERATOR_CHUNK_SIZE = 1000


@dataclass(frozen=True)
class _Failure:
    gateway_id: int
    error: str


@dataclass(frozen=True)
class _RunSummary:
    gateways: int
    succeeded: int
    failures: tuple[_Failure, ...]
    grants: int
    revokes: int
    unchanged: int

    @property
    def change_count(self) -> int:
        return self.grants + self.revokes


class Command(BaseCommand):
    help = "以本地 GatewayMember 为准，对账权限中心 V4 网关角色授权"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--gateway", help="仅对账指定网关 ID 或名称")
        parser.add_argument("--username", help="对所有现存网关仅对账指定用户")
        parser.add_argument("--all", action="store_true", help="对账全部现存网关")
        parser.add_argument("--apply", action="store_true", help="应用变更；不指定时仅输出 dry-run 计划")
        parser.add_argument(
            "--initial",
            action="store_true",
            help="首次部署全量同步；已成功执行过则跳过，仅可与 --all --apply 配合",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="跳过对账变更量限制",
        )
        parser.add_argument(
            "--max-changes",
            type=int,
            default=DEFAULT_MAX_CHANGES,
            help=f"普通 apply 允许的最大变更数，默认 {DEFAULT_MAX_CHANGES}",
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
        if not settings.BK_IAM_V4_ENABLED:
            self.stdout.write("BK_IAM_V4_ENABLED=false; skipped")
            return

        self._validate_arguments(options)
        initial_sync_context = GatewayIAMSyncContext()
        if options["initial"] and initial_sync_context.is_initial_sync_completed():
            self.stdout.write("gateway RBAC initial sync already completed; skipped")
            return

        operator = self._validate_settings()

        try:
            gateway_ids = self._get_gateway_ids(options)
            if options["apply"]:
                preflight = self._reconcile_gateways(
                    gateway_ids,
                    apply=False,
                    operator=operator,
                    username=options["username"],
                    page_size=options["page_size"],
                    gateway_delay=options["gateway_delay"],
                    phase="preflight",
                )
                self._write_summary(preflight, phase="preflight")
                self._raise_for_failures(preflight)
                if preflight.change_count > options["max_changes"] and not options["force"]:
                    raise CommandError(
                        f"计划变更数 {preflight.change_count} 超过 --max-changes={options['max_changes']}；"
                        "确认后使用 --force 执行"
                    )

            phase = "apply" if options["apply"] else "dry-run"
            summary = self._reconcile_gateways(
                gateway_ids,
                apply=options["apply"],
                operator=operator,
                username=options["username"],
                page_size=options["page_size"],
                gateway_delay=options["gateway_delay"],
                phase=phase,
            )
            self._write_summary(summary, phase=phase)
            self._raise_for_failures(summary)
            if options["initial"]:
                initial_sync_context.mark_initial_sync_completed()
                self.stdout.write("gateway RBAC initial sync marked as completed")
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
        if options["initial"] and not (options["all"] and options["apply"]):
            raise CommandError("--initial 必须与 --all --apply 配合使用")

        if not 1 <= options["page_size"] <= 100:
            raise CommandError("--page-size 必须在 1 到 100 之间")
        if options["max_changes"] < 0:
            raise CommandError("--max-changes 不能小于 0")
        if options["gateway_delay"] < 0:
            raise CommandError("--gateway-delay 不能小于 0")
        if options["username"] is not None and not options["username"].strip():
            raise CommandError("--username 不能为空")

    def _validate_settings(self) -> str:
        parsed_url = urlparse(settings.BK_IAM_V4_API_URL)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise CommandError("BK_IAM_V4_API_URL 必须是有效的 HTTP(S) URL")

        try:
            return get_gateway_iam_system_operator()
        except ValueError as exc:
            raise CommandError("BK_IAM_V4_MANAGERS 必须至少配置一个非空管理员") from exc

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
        phase: str,
    ) -> _RunSummary:
        synchronizer = GatewayIAMAuthorizationSynchronizer(page_size=page_size)
        failures: list[_Failure] = []
        succeeded = 0
        grants = 0
        revokes = 0
        unchanged = 0
        total = len(gateway_ids)

        for index, gateway_id in enumerate(gateway_ids, start=1):
            self.stdout.write(f"progress={index}/{total} gateway={gateway_id} phase={phase}")
            try:
                result = synchronizer.reconcile_gateway(
                    gateway_id,
                    apply=apply,
                    operator=operator,
                    username=username,
                )
            except Exception as err:
                failures.append(_Failure(gateway_id, str(err)))
                self.stderr.write(f"gateway={gateway_id} phase={phase} status=failed error={err}")
                if gateway_delay and index < total:
                    time.sleep(gateway_delay)
                continue

            succeeded += 1
            grants += result.grant_count
            revokes += result.revoke_count
            unchanged += result.unchanged
            self.stdout.write(
                f"gateway={result.gateway_id}:{result.gateway_name} "
                f"grants={result.grant_count} revokes={result.revoke_count} "
                f"unchanged={result.unchanged} applied={str(result.applied).lower()}"
            )
            for item in result.grants:
                self.stdout.write(
                    f"grant username={item.username} role={item.role} "
                    f"expired_at={item.expired_at} reason={item.reason}"
                )
            for item in result.revokes:
                self.stdout.write(
                    f"revoke username={item.username} role={item.role} "
                    f"expired_at={item.expired_at} reason={item.reason}"
                )
            if gateway_delay and index < total:
                time.sleep(gateway_delay)
        return _RunSummary(
            gateways=total,
            succeeded=succeeded,
            failures=tuple(failures),
            grants=grants,
            revokes=revokes,
            unchanged=unchanged,
        )

    def _write_summary(self, summary: _RunSummary, *, phase: str) -> None:
        self.stdout.write(
            f"summary phase={phase} gateways={summary.gateways} succeeded={summary.succeeded} "
            f"failed={len(summary.failures)} grants={summary.grants} "
            f"revokes={summary.revokes} unchanged={summary.unchanged}"
        )

    def _raise_for_failures(self, summary: _RunSummary) -> None:
        if not summary.failures:
            return
        error = "; ".join(f"gateway={failure.gateway_id} error={failure.error}" for failure in summary.failures)
        raise CommandError(f"网关 RBAC 权限对账失败: {error}")
