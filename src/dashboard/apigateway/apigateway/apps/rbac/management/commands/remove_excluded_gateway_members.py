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

from apigateway.apps.rbac.models import GatewayMember


class Command(BaseCommand):
    help = "删除多租户下配置为排除用户名的网关成员记录"

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--apply",
            action="store_true",
            help="执行删除，默认仅统计将删除的记录",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        if not settings.ENABLE_MULTI_TENANT_MODE:
            self.stdout.write("summary status=skipped reason=multi-tenant-disabled")
            return

        apply = options["apply"]
        queryset = GatewayMember.objects.filter(username__in=settings.BK_IAM_V4_EXCLUDED_USERNAMES)
        delete_count = queryset.count()
        if apply and delete_count:
            queryset.delete()
        self.stdout.write(f"summary delete={delete_count} apply={str(apply).lower()}")
