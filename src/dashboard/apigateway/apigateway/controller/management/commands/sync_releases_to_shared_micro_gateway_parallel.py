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
from multiprocessing import Pool
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError

import apigateway.controller.tasks.syncing as syncing
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)

POOL_SIZE = 10


def sync_gateway(gateway):
    # https://groups.google.com/g/django-users/c/eCAIY9DAfG0
    from django.db import connection

    connection.close()

    print(f"syncing release for gateway {gateway.name} ...")
    ok = syncing.rolling_update_release(gateway.id)
    if not ok:
        print(f"[ERROR] syncing release for gateway {gateway.name} failed")
        return gateway.name
    else:
        print(f"[INFO] syncing release for gateway {gateway.name} success")
        return None


class Command(BaseCommand):
    """同步已发布的资源到共享网关，只对存在且Activate状态的stage进行同步处理，非Activate stage与曾被删除的stage将忽略"""

    def add_arguments(self, parser):
        parser.add_argument("--api-names", dest="api_names", nargs="*", help="api names, default is all micro apis")

    def handle(self, api_names: Optional[List[str]], *args, **options):
        gateways = Gateway.objects.filter_micro_and_active_queryset()
        if api_names:
            gateways = gateways.filter(name__in=api_names)

        failed_gateway_names = []
        with Pool(POOL_SIZE) as pool:
            failed_gateway_names = pool.map(sync_gateway, gateways)
            failed_gateway_names = [name for name in failed_gateway_names if name is not None]

        if len(failed_gateway_names) != 0:
            raise CommandError("failed gateway: {}".format(", ".join(failed_gateway_names)))

        print("syncing gateway succeeded")
