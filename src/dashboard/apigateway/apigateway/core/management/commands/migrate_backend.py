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
from typing import Any, Dict

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from apigateway.biz.resource.importer.legacy_synchronizers import LegacyBackendCreator, LegacyUpstream
from apigateway.core.constants import DEFAULT_BACKEND_NAME, ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Backend, BackendConfig, Context, Gateway, Proxy, Stage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """将stage/resource的proxy配置迁移成Backend"""

    def handle(self, *args, **options):
        # 遍历gateway, 迁移proxy配置
        qs = Gateway.objects.all().order_by("id")

        logger.info("start migrate gateway backend, all gateway count %s", qs.count())

        paginator = Paginator(qs, 100)
        for i in paginator.page_range:
            logger.info("migrate gateway count %s", (i + 1) * 100)

            for gateway in paginator.page(i):
                self._handle_gateway(gateway)

        logger.info("finish migrate gateway backend")

    def _handle_gateway(self, gateway: Gateway):
        # 创建默认backend
        default_backend, _ = Backend.objects.get_or_create(gateway=gateway, name=DEFAULT_BACKEND_NAME)

        # 迁移 stage 的 proxy 配置
        stages = list(Stage.objects.filter(gateway=gateway))
        # 记录 stage 配置的 timeout, 用于后续 resource 的数据迁移
        stage_id_to_timeout: Dict[int, int] = {}

        for stage in stages:
            context = Context.objects.filter(
                scope_type=ContextScopeTypeEnum.STAGE.value,
                scope_id=stage.id,
                type=ContextTypeEnum.STAGE_PROXY_HTTP.value,
            ).first()

            if not context:
                continue

            config = context.config
            stage_id_to_timeout[stage.id] = config["timeout"]

            self._handle_stage_backend(gateway, stage, default_backend, config)

        legacy_backend_creator = LegacyBackendCreator(gateway=gateway, username="cli")

        # 迁移resource的proxy上游配置
        qs = Proxy.objects.filter(resource__gateway=gateway).all().order_by("id")
        paginator = Paginator(qs, 100)
        for i in paginator.page_range:
            for proxy in paginator.page(i):
                config = proxy.config
                if not config.get("upstreams"):
                    # 未配置自定义后端，关联 resource 到 default_backend
                    proxy.backend = default_backend
                    proxy.save()
                    continue

                legacy_upstream = LegacyUpstream(config["upstreams"])
                stage_id_to_backend_config = legacy_upstream.get_stage_id_to_backend_config(
                    stages, stage_id_to_timeout
                )

                backend = legacy_backend_creator.match_or_create_backend(stage_id_to_backend_config)
                proxy.backend = backend
                proxy.save()

    def _handle_stage_backend(
        self,
        gateway: Gateway,
        stage: Stage,
        backend: Backend,
        proxy_http_config: Dict[str, Any],
    ):
        hosts = []
        for host in proxy_http_config["upstreams"]["hosts"]:
            if host["host"]:
                scheme, _host = host["host"].rstrip("/").split("://")
                hosts.append({"scheme": scheme, "host": _host, "weight": host.get("weight", 100)})
            else:
                hosts.append({"scheme": "http", "host": "", "weight": 100})

        config = {
            "type": "node",
            "timeout": proxy_http_config["timeout"],
            "loadbalance": proxy_http_config["upstreams"]["loadbalance"],
            "hosts": hosts,
        }

        backend_config = BackendConfig.objects.filter(gateway=gateway, backend=backend, stage=stage).first()
        if not backend_config:
            backend_config = BackendConfig(
                gateway=gateway,
                backend=backend,
                stage=stage,
                config=config,
            )
        else:
            backend_config.config = config
        backend_config.save()
