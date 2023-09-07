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
from typing import List, Optional

from django.core.management.base import BaseCommand, CommandError

from apigateway.controller.tasks import syncing
from apigateway.core.constants import PublishSourceEnum
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """同步已发布的资源到共享网关，只对存在且Activate状态的stage进行同步处理，非Activate stage与曾被删除的stage将忽略"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--gateway-names", dest="gateway_names", nargs="*", help="gateway names, default is all micro apis"
        )

    def handle(self, gateway_names: Optional[List[str]], *args, **options):
        gateways = Gateway.objects.filter_micro_and_active_queryset()
        if gateway_names:
            gateways = gateways.filter(name__in=gateway_names)

        failed_gateway_names = []
        for gateway in gateways:
            print(f"syncing release for gateway {gateway.name} ...")
            # publish_id=-1 标识cli同步网关发布操作，方便operator过滤不上报
            ok = syncing.trigger_gateway_publish(
                PublishSourceEnum.CLI_SYNC, author="cli", gateway_id=gateway.id, is_sync=True
            )
            if not ok:
                print(f"[ERROR] syncing release for gateway {gateway.name} failed")
                failed_gateway_names.append(gateway.name)

        if len(failed_gateway_names) != 0:
            raise CommandError("failed gateway: {}".format(", ".join(failed_gateway_names)))

        print("syncing gateway succeeded")
