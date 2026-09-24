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
from dataclasses import dataclass
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError, CommandParser

from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.gateway import add_gateway_administrators
from apigateway.biz.iam import GatewayIAMAuthorizationSynchronizer, get_gateway_iam_system_operator
from apigateway.common.tenant.constants import TenantModeEnum
from apigateway.core.models import Gateway

MAX_USERNAME_LENGTH = 64


@dataclass(frozen=True)
class _Failure:
    gateway_id: int
    gateway_name: str
    error: str


class Command(BaseCommand):
    help = "为所有 tenant_mode=global 的网关批量增加管理员"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--gateway",
            help="指定网关 ID 或名称；不指定时处理全部 global 网关",
        )
        parser.add_argument(
            "--username",
            action="append",
            required=True,
            help="待添加管理员用户名，支持逗号分隔，也可重复指定多个 --username",
        )
        parser.add_argument(
            "--apply",
            action="store_true",
            help="执行写入，默认仅输出 dry-run 计划",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        usernames = self._normalize_usernames(options["username"])
        apply = options["apply"]
        iam_enabled = settings.BK_IAM_V4_ENABLED
        operator = self._resolve_operator(iam_enabled=iam_enabled) if apply else settings.GATEWAY_DEFAULT_CREATOR
        gateways = self._list_gateways(options["gateway"])
        if not gateways:
            self.stdout.write("no global gateways found; skipped")
            return

        planned = 0
        applied = 0
        unchanged = 0
        failures: list[_Failure] = []
        requested = set(usernames)
        synchronizer = GatewayIAMAuthorizationSynchronizer() if (apply and iam_enabled) else None
        for gateway in gateways:
            existing = set(GatewayMember.objects.list_gateway_administrators(gateway.id))
            local_change_required = not requested.issubset(existing)
            usernames_to_reconcile = sorted(requested & existing)
            if local_change_required:
                planned += 1
            else:
                unchanged += 1

            self.stdout.write(
                f"gateway={gateway.id}:{gateway.name} local_change={str(local_change_required).lower()} "
                f"administrators={usernames} apply={str(apply).lower()} iam_enabled={str(iam_enabled).lower()}"
            )
            if not apply:
                continue

            try:
                administrators = add_gateway_administrators(gateway, usernames, operator)
                iam_changes = 0
                if synchronizer is not None:
                    for username in usernames_to_reconcile:
                        result = synchronizer.reconcile_gateway(
                            gateway.id,
                            apply=True,
                            operator=operator,
                            username=username,
                        )
                        iam_changes += result.change_count
            except Exception as err:
                failures.append(_Failure(gateway.id, gateway.name, str(err)))
                self.stderr.write(f"gateway={gateway.id}:{gateway.name} status=failed error={err}")
                continue

            applied += 1
            self.stdout.write(
                f"gateway={gateway.id}:{gateway.name} status=applied administrators={administrators} "
                f"iam_reconciled_changes={iam_changes} iam_skipped={str(not iam_enabled).lower()}"
            )

        self.stdout.write(
            f"summary gateways={len(gateways)} planned={planned} applied={applied} unchanged={unchanged} "
            f"failed={len(failures)}"
        )
        if failures:
            error_message = "; ".join(
                f"gateway={failure.gateway_id}:{failure.gateway_name} error={failure.error}" for failure in failures
            )
            raise CommandError(f"批量添加 global 网关管理员失败: {error_message}")

    def _normalize_usernames(self, usernames: list[str]) -> list[str]:
        normalized = []
        for value in usernames:
            for username in value.split(","):
                candidate = username.strip()
                if not candidate:
                    raise CommandError("--username 不能为空")
                if len(candidate) > MAX_USERNAME_LENGTH:
                    raise CommandError(f"--username 长度不能超过 {MAX_USERNAME_LENGTH}")
                normalized.append(candidate)
        return sorted(set(normalized))

    def _resolve_operator(self, *, iam_enabled: bool) -> str:
        if not iam_enabled:
            return settings.GATEWAY_DEFAULT_CREATOR

        try:
            return get_gateway_iam_system_operator()
        except ValueError as err:
            raise CommandError("BK_IAM_V4_MANAGERS 必须至少配置一个非空管理员") from err

    def _list_gateways(self, gateway_selector: str | None) -> list[Gateway]:
        queryset = Gateway.objects.filter(tenant_mode=TenantModeEnum.GLOBAL.value).order_by("id")
        if gateway_selector is None:
            return list(queryset)

        gateway_id = None
        try:
            parsed_gateway_id = int(gateway_selector)
        except TypeError, ValueError:
            pass
        else:
            gateway_id = queryset.filter(id=parsed_gateway_id).values_list("id", flat=True).first()
        if gateway_id is None:
            gateway_id = queryset.filter(name=gateway_selector).values_list("id", flat=True).first()
        if gateway_id is None:
            raise CommandError(f"global 网关不存在: {gateway_selector}")

        return list(queryset.filter(id=gateway_id))
