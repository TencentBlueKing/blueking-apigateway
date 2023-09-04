# -*- coding: utf-8 -*-
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

from apigateway.core.constants import ProxyTypeEnum
from apigateway.core.models import Gateway, Proxy, Resource

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    删除重复的资源 proxy

    - 删除未使用的 proxy 数据
    """

    def add_arguments(self, parser):
        parser.add_argument("--gateway-name", type=str, dest="gateway_name")
        parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="dry run")

    def handle(self, gateway_name: Optional[str], dry_run: bool, **options):
        for gateway_id in self._get_gateway_ids(gateway_name):
            resource_id_to_proxy_id = dict(
                # proxy_id 为 0，为新版资源配置，不需要清理
                Resource.objects.filter(gateway_id=gateway_id)
                .exclude(proxy_id=0)
                .values_list("id", "proxy_id")
            )
            proxies = {
                proxy.id: proxy for proxy in Proxy.objects.filter(resource_id__in=resource_id_to_proxy_id.keys())
            }

            for proxy_id in resource_id_to_proxy_id.values():
                proxies.pop(proxy_id)

            if not proxies:
                continue

            not_mock_proxies = [proxy for proxy in proxies.values() if proxy.type != ProxyTypeEnum.MOCK.value]
            if not_mock_proxies:
                raise CommandError(
                    "For gateway (id={gateway_id}), proxies are not mock type, please check:\n{proxies}".format(
                        gateway_id=gateway_id,
                        proxies="\n".join(
                            f"id={proxy.id}, resource_id={proxy.resource_id}, type={proxy.type}"
                            for proxy in proxies.values()
                        ),
                    )
                )

            print(
                "For gateway (id={gateway_id}), the following proxies are not in used and will be deleted, proxies:\n{proxies}".format(
                    gateway_id=gateway_id,
                    proxies="\n".join(
                        [
                            f"id={proxy.id}, resource_id={proxy.resource_id}, type={proxy.type}"
                            for proxy in proxies.values()
                        ]
                    ),
                )
            )
            if dry_run:
                continue

            Proxy.objects.filter(id__in=proxies.keys()).delete()

        print("Done")

    def _get_gateway_ids(self, gateway_name: Optional[str]) -> List[int]:
        if not gateway_name:
            return list(Gateway.objects.all().values_list("id", flat=True))

        return list(Gateway.objects.filter(name=gateway_name).values_list("id", flat=True))
