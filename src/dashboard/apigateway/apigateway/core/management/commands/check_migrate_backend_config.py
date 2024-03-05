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
from typing import Any, Dict

from django.core.management.base import BaseCommand

from apigateway.core.constants import DEFAULT_BACKEND_NAME, ContextScopeTypeEnum, ContextTypeEnum
from apigateway.core.models import Backend, BackendConfig, Context, Gateway, Proxy, Stage


class Command(BaseCommand):
    """检查 stage/resource 的 proxy 配置是否已正确迁移到 Backend,1.14会移除"""

    def handle(self, *args, **options):
        self.check_gateway_backend_migration()

    def check_gateway_backend_migration(self):
        gateways = Gateway.objects.all().order_by("id")
        total_gateways = gateways.count()
        failed_gateways = 0

        self.stdout.write("Starting to check gateway backend migration")

        for gateway in gateways:
            if not self._check_gateway_backend(gateway):
                failed_gateways += 1
                self.stdout.write(f"Gateway {gateway.id} backend migration check failed")

        self.stdout.write(
            f"Finished checking gateway backend migration: {total_gateways} checked, {failed_gateways} failed"
        )

    def _check_gateway_backend(self, gateway: Gateway) -> bool:
        # 检查默认后端是否存在
        default_backend_exists = Backend.objects.filter(gateway=gateway, name=DEFAULT_BACKEND_NAME).exists()
        if not default_backend_exists:
            self.stdout.write(f"Default backend for gateway {gateway.id} does not exist")
            return False

        # 检查 stage 后端配置
        stages = Stage.objects.filter(gateway=gateway)
        for stage in stages:
            if not self._check_stage_backend(gateway, stage):
                return False

        # 检查 proxy 后端配置
        proxies = Proxy.objects.filter(resource__gateway=gateway).all()
        return all(self._check_proxy_backend(gateway, proxy) for proxy in proxies)

    def _check_stage_backend(self, gateway: Gateway, stage: Stage) -> bool:
        context = Context.objects.filter(
            scope_type=ContextScopeTypeEnum.STAGE.value,
            scope_id=stage.id,
            type=ContextTypeEnum.STAGE_PROXY_HTTP.value,
        ).first()

        if not context:
            # 如果没有上下文，则这个阶段不应该有后端配置
            backend_config_exists = BackendConfig.objects.filter(gateway=gateway, stage=stage).exists()
            if backend_config_exists:
                self.stdout.write(
                    f"Gateway {gateway.id} Backend config should not config for stage "
                    f"{stage.id} for no context proxy"
                )
            return not backend_config_exists

        # 比较预期的后端配置和实际的后端配置
        expected_config = self._generate_expected_backend_config(context.config)
        actual_backend_config = BackendConfig.objects.filter(gateway=gateway, stage=stage).first()

        if not actual_backend_config or actual_backend_config.config != expected_config:
            self.stdout.write(f"Backend config for stage {stage.id} does not match the expected config")
            self.stdout.write(f"Expected config: {expected_config}")
            self.stdout.write(f"Actual config: {actual_backend_config.config if actual_backend_config else 'None'}")
            return False

        return True

    def _check_proxy_backend(self, gateway: Gateway, proxy: Proxy) -> bool:
        # 如果 proxy 没有自定义后端，它应该取默认后端
        if not proxy.config.get("upstreams"):
            no_diff = proxy.backend.name == DEFAULT_BACKEND_NAME
            if not no_diff:
                self.stdout.write(
                    f"Gateway {gateway.id} proxy backend name should be {DEFAULT_BACKEND_NAME}"
                    f"proxy {proxy.id} for no upstreams proxy"
                )
            return no_diff

        # 自定义后端应该存在并且与预期配置匹配
        expected_config = self._generate_expected_backend_config(proxy.config)
        actual_backend_config = BackendConfig.objects.filter(gateway=gateway, backend=proxy.backend).first()

        if not actual_backend_config or actual_backend_config.config != expected_config:
            self.stdout.write(f"Backend config for proxy {proxy.id} does not match the expected config")
            self.stdout.write(f"Expected config: {expected_config}")
            self.stdout.write(f"Actual config: {actual_backend_config.config if actual_backend_config else 'None'}")
            return False

        return True

    def _generate_expected_backend_config(self, proxy_http_config: Dict[str, Any]) -> Dict[str, Any]:
        # 根据 proxy_http_config 生成预期的后端配置
        hosts = []
        for host in proxy_http_config["upstreams"]["hosts"]:
            if host["host"]:
                scheme, _host = host["host"].rstrip("/").split("://")
                hosts.append({"scheme": scheme, "host": _host, "weight": host["weight"]})
            else:
                hosts.append({"scheme": "http", "host": "", "weight": host["weight"]})

        return {
            "type": "node",
            "timeout": proxy_http_config["timeout"],
            "loadbalance": proxy_http_config["upstreams"]["loadbalance"],
            "hosts": hosts,
        }
