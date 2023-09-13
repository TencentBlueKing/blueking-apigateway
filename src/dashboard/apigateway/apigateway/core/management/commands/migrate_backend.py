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
import re
from typing import Any, Dict, List, Tuple

from django.core.management.base import BaseCommand
from django.core.paginator import Paginator

from apigateway.core.constants import DEFAULT_BACKEND_NAME, ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Backend, BackendConfig, Context, Gateway, Proxy, Stage

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """将stage/resource的proxy配置迁移成Backend"""

    def handle(self, *args, **options):
        # 遍历gateway, 迁移proxy配置
        qs = Gateway.objects.all()

        logger.info("start migrate gateway backend, all gateway count %s", qs.count())

        paginator = Paginator(qs, 100)
        for i in paginator.page_range:
            logger.info("migrate gateway count %s", (i + 1) * 100)

            for gateway in paginator.page(i):
                self._handle_gateway(gateway)

        logger.info("finish migrate gateway backend")

    def _handle_gateway(self, gateway: Gateway):
        # 创建默认backend
        default_backend, _ = Backend.objects.get_or_create(
            gateway=gateway,
            name=DEFAULT_BACKEND_NAME,
        )

        # 迁移stage的proxy配置
        stages = list(Stage.objects.filter(gateway=gateway))
        # 记录stage配置的timeout, 用于后续resource的数据迁移
        stage_timeout: Dict[int, int] = {}
        for stage in stages:
            context = Context.objects.filter(
                scope_type=ContextScopeTypeEnum.STAGE.value,
                scope_id=stage.id,
                type=ContextTypeEnum.STAGE_PROXY_HTTP.value,
            ).first()

            if not context:
                continue

            config = context.config
            self._handle_stage_backend(gateway, stage, default_backend, config)

            stage_timeout[stage.id] = config["timeout"]

        # config 与已创建 backend 映射
        config_backend: Dict[Tuple, Backend] = {}

        resource_backend_count = 0
        # 迁移resource的proxy上游配置
        qs = Proxy.objects.filter(resource__gateway=gateway).all()
        paginator = Paginator(qs, 100)
        for i in paginator.page_range:
            for proxy in paginator.page(i):
                config = proxy.config
                if "upstreams" not in config or not config["upstreams"]:
                    # 关联resource与default_backend
                    proxy.backend = default_backend
                    proxy.save()
                    continue

                # 已有相同的backend
                config_hash_tuple = self._get_config_hash_tuple(config)
                if config_hash_tuple in config_backend:
                    backend = config_backend[config_hash_tuple]
                    # 关联resource与backend
                    proxy.backend = backend
                    proxy.save()
                    continue

                resource_backend_count += 1
                backend = self._handle_resource_backend(gateway, stages, stage_timeout, config, resource_backend_count)
                # 关联resource与backend
                proxy.backend = backend
                proxy.save()

                config_backend[config_hash_tuple] = backend

        # 清理未使用的backend
        used_backend_ids = list(
            Proxy.objects.filter(resource__gateway=gateway).values_list("backend_id", flat=True).distinct()
        )
        used_backend_ids.append(default_backend.id)

        # 查询排除了已使用的backend, 并且名称中包含backend-的backend, 用于清理上一次迁移现在重复的backend
        delete_backend_ids = list(
            Backend.objects.exclude(id__in=used_backend_ids)
            .filter(gateway=gateway, name__startswith="backend-")
            .values_list("id", flat=True)
        )

        if delete_backend_ids:
            BackendConfig.objects.filter(backend_id__in=delete_backend_ids).delete()
            Backend.objects.filter(id__in=delete_backend_ids).delete()

    def _handle_resource_backend(
        self,
        gateway: Gateway,
        stages: List[Stage],
        stage_timeout: Dict[int, int],
        proxy_http_config: Dict[str, Any],
        resource_backend_count: int,
    ) -> Backend:
        backend = Backend.objects.create(
            gateway=gateway,
            name=f"backend-{resource_backend_count}",
        )

        backend_configs = []
        for stage in stages:
            vars = stage.vars

            hosts = []
            for host in proxy_http_config["upstreams"]["hosts"]:
                scheme, _host = host["host"].split("://")

                # 渲染host中的环境变量
                matches = re.findall(r"\{env.(\w+)\}", _host)
                for key in matches:
                    if key in vars:
                        _host = _host.replace("{env." + key + "}", vars[key])

                hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})

            config = {
                "type": "node",
                "timeout": stage_timeout[stage.id],
                "loadbalance": proxy_http_config["upstreams"]["loadbalance"],
                "hosts": hosts,
            }

            backend_config = BackendConfig(
                gateway=gateway,
                backend=backend,
                stage=stage,
                config=config,
            )
            backend_configs.append(backend_config)

        if backend_configs:
            BackendConfig.objects.bulk_create(backend_configs)

        return backend

    def _get_config_hash_tuple(self, proxy_http_config: Dict[str, Any]):
        hosts = sorted(proxy_http_config["upstreams"]["hosts"], key=lambda x: x["host"])
        return (
            proxy_http_config["upstreams"]["loadbalance"],
            tuple([(host["host"], host["weight"]) for host in hosts]),
        )

    def _handle_stage_backend(
        self, gateway: Gateway, stage: Stage, backend: Backend, proxy_http_config: Dict[str, Any]
    ):
        hosts = []
        for host in proxy_http_config["upstreams"]["hosts"]:
            if host["host"]:
                scheme, _host = host["host"].split("://")
                hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})
            else:
                hosts.append({"scheme": "http", "host": "", "weight": host["weight"]})

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
