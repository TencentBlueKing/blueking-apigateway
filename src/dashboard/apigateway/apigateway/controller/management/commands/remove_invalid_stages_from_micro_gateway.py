#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
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
from typing import List, Set, Tuple

import etcd3
from django.conf import settings
from django.core.management.base import BaseCommand

from apigateway.core.constants import GatewayStatusEnum
from apigateway.core.models import Gateway, MicroGateway, Stage
from apigateway.utils.etcd import get_etcd_client

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """该命令主要用于删除共享网关（etcd）中的“非法”数据，判断标准：

    1. 所属的网关环境，在数据库中的状态为非“Activate”
    2. 所属的网关环境，在数据库中已被删除

    本命令涉及数据删除，属于敏感操作。
    """

    client: etcd3.Etcd3Client = get_etcd_client()

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Run full syncing without ETCD modification operation",
        )

    def handle(self, dry_run, *args, **options):
        self.dry_run = dry_run

        gateways = Gateway.objects.filter(status=GatewayStatusEnum.ACTIVE.value)
        shared_gateway = MicroGateway.objects.get_default_shared_gateway()

        num_of_keys = self._delete_invalid_stages(gateways, shared_gateway)
        self.stdout.write(f"Total number of deleted keys: {num_of_keys}")

    def _delete_invalid_stages(self, gateways: List[Gateway], micro_gateway: MicroGateway) -> int:
        """Loop over all data stored in the gateway-local storage (etcd), find out those
        absent in the database or obsolete, then remove these keys.

        :return: The number of removed etcd keys.
        """
        self.stdout.write("Starting to find invalid gateway and stages in etcd...")
        active_stages_by_gw = Stage.objects.get_gateway_name_to_active_stage_names(gateways)
        prefix = f"{settings.BK_GATEWAY_ETCD_NAMESPACE_PREFIX}/{micro_gateway.name}"

        # Format: (<gateway name>, <stage name>)
        invalid_stages: Set[Tuple[str, str]] = set()

        # Iterate through all the gateway-related keys in etcd and find invalid stages.
        # Keys sharing the same stage name will only be processed once, since the deletion
        # was performed using the prefix instead of the exact key.
        for _, meta in self.client.get_prefix(key_prefix=prefix + "/", keys_only=True):
            key_without_prefix = meta.key.decode("utf-8")[len(prefix) :]
            # The key format: /<get_prefix>/<gateway>/<stage>/<api-version>/<kind>/<name>
            gw_name, stage, *_ = key_without_prefix.strip("/").split("/")

            if (gw_name, stage) in invalid_stages:
                continue

            # Check if the gateway and stage is invalid
            if gw_name not in active_stages_by_gw or stage not in active_stages_by_gw[gw_name]:
                self.stdout.write(
                    f'Found a key owned by invalid stage: "{gw_name}/{stage}", will remove it and related keys.',
                    self.style.WARNING,
                )
                invalid_stages.add((gw_name, stage))

        if not invalid_stages:
            self.stdout.write("Can't find any keys owned by invalid stages, skip deletion.", self.style.SUCCESS)
            return 0

        # Perform the deletion using etcd client
        num_of_keys = 0
        for gw_name, stage in invalid_stages:
            # Restore the etcd key by gw and stage names
            delete_prefix = f"{prefix}/{gw_name}/{stage}/"
            if self.dry_run:
                self.stdout.write(f'(dry-run) Skip deletion on "{delete_prefix}"...')
                continue

            resp = self.client.delete_prefix(delete_prefix)

            # Print a warning message if no keys can be deleted for given prefix(which shouldn't happen)
            if resp.deleted <= 1:
                self.stdout.write(f'No keys have been deleted for prefix: "{delete_prefix}"', self.style.WARNING)
            num_of_keys += resp.deleted
        return num_of_keys
