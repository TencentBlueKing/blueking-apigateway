#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2025 Tencent. All rights reserved.
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

import base64
from typing import Dict, List, Union

from django.conf import settings
from django.utils.encoding import force_bytes, force_str

from apigateway.common.constants import DEFAULT_BACKEND_HOST_FOR_MISSING
from apigateway.controller.models import (
    BaseUpstream,
    GatewayApisixModel,
    Node,
    Plugin,
    Service,
    Timeout,
)
from apigateway.controller.models.constants import UpstreamSchemeEnum, UpstreamTypeEnum
from apigateway.controller.release_data import ReleaseData
from apigateway.core.models import Backend

from .base import GatewayResourceConvertor
from .constants import LABEL_KEY_BACKEND_ID, LABEL_KEY_PUBLISH_ID
from .utils import UrlInfo, truncate_string


class ServiceConvertor(GatewayResourceConvertor):
    def __init__(self, release_data: ReleaseData, publish_id: Union[int, None] = None):
        super().__init__(release_data)
        self._publish_id = publish_id

    def convert(self) -> List[GatewayApisixModel]:
        # FIXME: should not generate service if the backend is not related to any resource
        backend_configs = self._release_data.get_stage_backend_configs()
        if not backend_configs:
            return []

        # {
        #   "type": "node",
        #   "timeout": 60,
        #   "loadbalance": "roundrobin",
        #   "hosts": [
        #     {
        #       "scheme": "http",
        #       "host": "exmple.com",
        #       "weight": 100
        #     }
        #   ]
        # }

        services: List[GatewayApisixModel] = []
        # FIXME: 这里有没有环境变量渲染？

        for backend_id, backend_config in backend_configs.items():
            timeout = backend_config.get("timeout", 60)
            upstream = BaseUpstream(
                type=UpstreamTypeEnum.ROUNDROBIN,
                timeout=Timeout(
                    connect=timeout,
                    send=timeout,
                    read=timeout,
                ),
            )
            hosts = backend_config.get("hosts", [])
            if not hosts:
                raise ValueError(f"backend {backend_id} has no hosts")

            for node in hosts:
                host = node["host"]
                # 如果 default 没有设置 host，则默认使用 your-backend-host 来替代，避免 apisix 加载报错
                if host == "":
                    host = DEFAULT_BACKEND_HOST_FOR_MISSING
                if "scheme" in node:
                    host = node["scheme"] + "://" + host
                url_info = UrlInfo(host)

                try:
                    upstream.scheme = UpstreamSchemeEnum(url_info.scheme)
                except ValueError:
                    raise ValueError(
                        f"scheme {url_info.scheme!r} of host {node['host']!r} is not a valid UpstreamSchemeEnum"
                    )

                upstream.nodes.append(Node(host=url_info.domain, port=url_info.port, weight=node.get("weight", 1)))

            # FIXME: 如何处理 http/https 协议
            # FIXME: 环境变量渲染是不是 service 也有？

            stage_description = self.stage.description

            backend = Backend.objects.get(id=backend_id)
            backend_name = backend.name
            backend_description = backend.description

            description = f"{self.stage_name}/{self.stage_id}"
            if stage_description:
                description += f": {stage_description[:32]}"
            description += f" (backend={backend_name}"
            if backend_description:
                description += f": {backend_description[:32]}"
            description += ")"

            # currently, only add one plugin for service of per backend
            # other plugins are shared by stage, they will be merged on operator
            plugins: Dict[str, Plugin] = {
                "bk-backend-context": Plugin(bk_backend_id=backend_id, bk_backend_name=backend_name),
            }
            service_plugins = self._build_service_plugins()
            plugins.update(service_plugins)

            # stage_name max length is 20, stage_id 6, backend_id is 4, other 10
            # total max length is 64, so the buffer is 24 ( stage_id length + backend_id length)
            labels = self.get_gateway_resource_labels()
            if self._publish_id:
                labels.add_label(LABEL_KEY_PUBLISH_ID, str(self._publish_id))

            labels.add_label(LABEL_KEY_BACKEND_ID, str(backend_id))

            services.append(
                Service(
                    # FIXME:
                    # the previous id is: {gateway_name}.{stage_name}.{stage_id}-{backend_id}
                    # 30+1+20+1+ x + 1 + y = 53 + x + y, so x + y <= 11 (almost no buffer)
                    # so we should make a new id here?
                    # example: bk-apigateway-inner.prod.stage-6-backend-7
                    id=f"s-{self.stage_id}-b-{backend_id}",
                    name=truncate_string(f"{self.gateway_name}.{self.stage_name}.{backend_name}", 100),
                    desc=description,
                    labels=labels,
                    plugins=plugins,
                    upstream=upstream,
                )
            )

        return services

    def _build_service_plugins(self) -> Dict[str, Plugin]:
        plugins: Dict[str, Plugin] = self._get_stage_default_plugins()

        plugins.update(self._get_stage_binding_plugins())
        plugins.update(self._get_stage_extra_plugins())

        return plugins

    def _get_stage_default_plugins(self) -> Dict[str, Plugin]:
        """Get the default plugins for stage, which is shared by all resources in the stage"""
        default_plugins: Dict[str, Plugin] = {
            # 2024-08-19 disable the bk-opentelemetry plugin, we should let each gateway set their own opentelemetry
            # Plugin(name="bk-opentelemetry"),
            "prometheus": Plugin(),
            "bk-real-ip": Plugin(),
            "bk-auth-validate": Plugin(),
            "bk-auth-verify": Plugin(),
            "bk-break-recursive-call": Plugin(),
            "bk-delete-sensitive": Plugin(),
            "bk-log-context": Plugin(),
            "bk-delete-cookie": Plugin(),
            "bk-error-wrapper": Plugin(),
            "bk-jwt": Plugin(),
            "bk-request-id": Plugin(),
            "bk-response-check": Plugin(),
            "bk-permission": Plugin(),
            "bk-debug": Plugin(),
            "file-logger": Plugin(path="logs/access.log"),
            "bk-stage-context": Plugin(
                bk_gateway_name=self.gateway_name,
                bk_gateway_id=self.gateway_id,
                bk_stage_name=self.stage_name,
                jwt_private_key=force_str(base64.b64encode(force_bytes(self._release_data.jwt_private_key))),
                bk_api_auth=self._release_data.gateway_auth_config,
            ),
        }

        if settings.GATEWAY_CONCURRENCY_LIMIT_ENABLED:
            default_plugins["bk-concurrency-limit"] = Plugin()

        # 多租户模式
        if settings.ENABLE_MULTI_TENANT_MODE:
            default_plugins.update(
                {
                    "bk-tenant-verify": Plugin(),
                    "bk-tenant-validate": Plugin(
                        tenant_mode=self.gateway.tenant_mode, tenant_id=self.gateway.tenant_id
                    ),
                }
            )
        else:
            default_plugins["bk-default-tenant"] = Plugin()

        return default_plugins

    def _get_stage_binding_plugins(self) -> Dict[str, Plugin]:
        return {
            plugin_data.name: Plugin(**plugin_data.config) for plugin_data in self._release_data.get_stage_plugins()
        }

    def _get_stage_extra_plugins(self) -> Dict[str, Plugin]:
        if self.gateway_name in settings.LEGACY_INVALID_PARAMS_GATEWAY_NAMES:
            return {"bk-legacy-invalid-params": Plugin()}
        return {}
