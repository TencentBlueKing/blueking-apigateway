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
from multiprocessing import Pool
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apigateway.controller.publisher import publish
from apigateway.core.constants import GatewayStatusEnum, PublishSourceEnum
from apigateway.core.models import Gateway, Release, ReleaseHistory

logger = logging.getLogger(__name__)

POOL_SIZE = 10


def sync_gateway(gateway):
    # https://groups.google.com/g/django-users/c/eCAIY9DAfG0
    from django.db import connection  # noqa

    connection.close()

    print(f"syncing release for gateway {gateway.name} ...")
    try:
        ok = publish.trigger_gateway_publish(
            PublishSourceEnum.CLI_SYNC, author="cli", gateway_id=gateway.id, is_sync=True
        )
    except Exception:
        logger.exception("syncing release for gateway %s failed with exception", gateway.name)
        print(f"[ERROR] syncing release for gateway {gateway.name} failed")
        return gateway.name

    if not ok:
        print(f"[ERROR] syncing release for gateway {gateway.name} failed")
        return gateway.name

    print(f"[INFO] syncing release for gateway {gateway.name} success")
    return None


class Command(BaseCommand):
    """同步已发布的资源到共享网关，只对存在且Activate状态的stage进行同步处理，非Activate stage与曾被删除的stage将忽略"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--gateway-names", dest="gateway_names", nargs="*", help="gateway names, default is all micro apis"
        )
        parser.add_argument(
            "--released-since",
            dest="released_since",
            help=(
                "only sync gateways having release history created, or a release distributed, at or after "
                "this time, ISO 8601 such as 2026-11-17T10:00:00+08:00; a naive time uses settings.TIME_ZONE"
            ),
        )
        parser.add_argument(
            "--dry-run",
            dest="dry_run",
            action="store_true",
            help=(
                "print matched gateway names separated by spaces, without publishing; "
                "the output is empty when nothing matches"
            ),
        )

    def handle(
        self,
        *args,
        gateway_names: Optional[List[str]] = None,
        released_since: Optional[str] = None,
        dry_run: bool = False,
        **options,
    ):
        gateways = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value)
        if gateway_names:
            gateways = gateways.filter(name__in=gateway_names)
        if released_since:
            since = self._parse_released_since(released_since)
            # ReleaseHistory 覆盖版本发布及插件、后端服务变更触发的发布；
            # CLI_SYNC 等下发不写 ReleaseHistory，但下发成功会更新 Release.updated_time
            gateways = gateways.filter(
                Q(id__in=ReleaseHistory.objects.filter(created_time__gte=since).values("gateway_id"))
                | Q(id__in=Release.objects.filter(updated_time__gte=since).values("gateway_id"))
            )

        if dry_run:
            names = sorted(gateways.values_list("name", flat=True))
            self.stderr.write(f"{len(names)} gateways matched")
            self.stdout.write(" ".join(names))
            return

        failed_gateway_names = []
        with Pool(POOL_SIZE) as pool:
            failed_gateway_names = pool.map(sync_gateway, gateways)
            failed_gateway_names = [name for name in failed_gateway_names if name is not None]

        if len(failed_gateway_names) != 0:
            raise CommandError("failed gateway: {}".format(", ".join(failed_gateway_names)))

        print("syncing gateway succeeded")

    @staticmethod
    def _parse_released_since(value: str):
        try:
            since = parse_datetime(value)
        except ValueError:
            since = None
        if since is None:
            raise CommandError(f"invalid --released-since: {value}")
        if timezone.is_naive(since):
            since = timezone.make_aware(since)
        return since
