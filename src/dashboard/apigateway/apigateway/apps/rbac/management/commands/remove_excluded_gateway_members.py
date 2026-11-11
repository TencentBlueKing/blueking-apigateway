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
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

from apigateway.biz.gateway import remove_excluded_gateway_members
from apigateway.core.models import Gateway


class Command(BaseCommand):
    help = "删除多租户下配置为排除用户名的网关成员"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="执行删除，默认仅输出 dry-run 计划",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.ENABLE_MULTI_TENANT_MODE:
            self.stdout.write("summary status=skipped reason=multi-tenant-disabled")
            return

        apply = options["apply"]
        operator = settings.GATEWAY_DEFAULT_CREATOR
        affected = 0
        delete_count = 0
        skipped_count = 0
        for gateway in Gateway.objects.order_by("id"):
            result = remove_excluded_gateway_members(gateway, operator, apply=apply)
            if not result.delete_usernames and not result.skipped_last_administrators:
                continue

            affected += 1
            delete_count += len(result.delete_usernames)
            skipped_count += len(result.skipped_last_administrators)
            delete_usernames = ",".join(result.delete_usernames) or "-"
            skipped_usernames = ",".join(result.skipped_last_administrators) or "-"
            self.stdout.write(
                f"gateway={gateway.id}:{gateway.name} apply={str(apply).lower()} "
                f"delete={delete_usernames} skipped_last_administrators={skipped_usernames}"
            )

        self.stdout.write(
            f"summary gateways={affected} delete={delete_count} "
            f"skipped_last_administrators={skipped_count} apply={str(apply).lower()}"
        )
