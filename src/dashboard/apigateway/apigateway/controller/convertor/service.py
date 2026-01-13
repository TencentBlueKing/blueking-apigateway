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
from typing import Dict, List, Optional

from django.conf import settings
from django.utils.encoding import force_bytes, force_str

from apigateway.common.constants import DEFAULT_BACKEND_HOST_FOR_MISSING
from apigateway.controller.models import (
    ActiveCheck,
    ActiveHealthy,
    ActiveUnhealthy,
    BaseUpstream,
    Check,
    GatewayApisixModel,
    Node,
    PassiveCheck,
    PassiveHealthy,
    PassiveUnhealthy,
    Plugin,
    Service,
    Timeout,
)
from apigateway.controller.models.constants import (
    CheckActiveTypeEnum,
    CheckPassiveTypeEnum,
    UpstreamHashOnEnum,
    UpstreamSchemeEnum,
    UpstreamTypeEnum,
)
from apigateway.controller.release_data import ReleaseData
from apigateway.controller.uri_render import URIRender
from apigateway.core.constants import LoadBalanceTypeEnum
from apigateway.core.models import Backend

from .base import GatewayResourceConvertor
from .constants import LABEL_KEY_BACKEND_ID
from .utils import UrlInfo, truncate_string


class ServiceConvertor(GatewayResourceConvertor):
    def __init__(self, release_data: ReleaseData, publish_id: int, revoke_flag: Optional[bool] = False):
        super().__init__(release_data=release_data, publish_id=publish_id)
        self._revoke_flag = revoke_flag

    def convert(self) -> List[GatewayApisixModel]:
        # if revoke, we should not generate service, will delete the service from etcd
        if self._revoke_flag:
            return []

        # FIXME: should not generate service if the backend is not related to any resource
        backend_configs = self._release_data.get_stage_backend_configs()
        if not backend_configs:
            return []

        # {
        #   "type": "node",
        #   "timeout": 60,
        #   "loadbalance": "roundrobin", # or "chash"
        #   "hash_on": "header",
        #   "key": "content-type",
        #   "hosts": [
        #     {
        #       "scheme": "http",
        #       "host": "exmple.com",
        #       "weight": 100
        #     }
        #   ]
        # }

        services: List[GatewayApisixModel] = []

        for backend_id, backend_config in backend_configs.items():
            timeout = backend_config.get("timeout", 60)
            loadbalance_type = backend_config.get("loadbalance", UpstreamTypeEnum.ROUNDROBIN.value)
            # while the apisix has no wrr, we convert it to roundrobin, the weight would be set below
            if loadbalance_type == LoadBalanceTypeEnum.WRR.value:
                loadbalance_type = UpstreamTypeEnum.ROUNDROBIN.value

            upstream = BaseUpstream(
                type=UpstreamTypeEnum(loadbalance_type),
                timeout=Timeout(
                    connect=timeout,
                    send=timeout,
                    read=timeout,
                ),
            )
            if loadbalance_type == UpstreamTypeEnum.CHASH.value:
                upstream.hash_on = UpstreamHashOnEnum(backend_config.get("hash_on", UpstreamHashOnEnum.VARS.value))
                upstream.key = backend_config.get("key", "")

            hosts = backend_config.get("hosts", [])
            if not hosts:
                raise ValueError(f"backend {backend_id} has no hosts")

            # FIXME: check from backend_config and add tls.client_cert_id here, and build the name of ssl

            for node in hosts:
                host = node["host"]
                # 如果 default 没有设置 host，则默认使用 your-backend-host 来替代，避免 apisix 加载报错
                if host == "":
                    host = DEFAULT_BACKEND_HOST_FOR_MISSING
                # render the host with stage variables
                host = URIRender().render(host, self.stage.vars)

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

            # Convert checks if present
            checks_data = backend_config.get("checks")
            if checks_data:
                upstream.checks = self._convert_checks(checks_data)

            # FIXME: 如何处理 http/https 协议
            backend = Backend.objects.get(id=backend_id)
            backend_name = backend.name
            # backend_desc = backend.description

            # currently, only add one plugin for service of per backend
            # other plugins are shared by stage, they will be merged on operator
            plugins: Dict[str, Plugin] = {
                "bk-backend-context": Plugin(bk_backend_id=backend_id, bk_backend_name=backend_name),
            }
            service_plugins = self._build_service_plugins()
            plugins.update(service_plugins)

            # stage_name max length is 20, stage_id 6, backend_id is 4, other 10
            # total max length is 64, so the buffer is 24 ( stage_id length + backend_id length)
            labels = self.get_labels()

            # for build the mapping of backend_id to service_id
            labels.add_label(LABEL_KEY_BACKEND_ID, str(backend_id))

            services.append(
                Service(
                    # the previous id is: {gateway_name}.{stage_name}.{stage_id}-{backend_id}
                    # the stage_id + backend_id is unique, so we can make the prefix smaller enough to keep the id length < 64
                    # example: bk-apigateway-inner.prod.6-7
                    # 30 + 1 + 20 + 1 + x + 1 + y = 53 + x + y, so x + y <= 11 (almost no buffer)
                    # so we truncate the stage_name to 10
                    # 30 + 1 + 10 + 1 + x + 1 + y = 43 + x + y, so x + y <= 21 (enough buffer)
                    id=f"{self.gateway_name}.{self.stage_name[:10]}.{self.stage_id}-{backend_id}",
                    # length is: 30 + 1 + 20 + 1 + 20 = 72
                    name=truncate_string(
                        f"{self.gateway_name}.{self.stage_name}.{backend_name}",
                        100,
                    ),
                    # NOTE: no desc for service, save memory
                    # desc=truncate_string(
                    #     f"[{self.stage_name}/{self.stage_id}, {backend_name}/{backend_id}] {backend_desc}",
                    #     100,
                    # ),
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

    def _convert_checks(self, checks_data: Dict) -> Check:
        """Convert backend_config checks dict to controller Check model

        Args:
            checks_data: Dict from backend_config, e.g.:
                {
                    "active": {
                        "type": "http",
                        "timeout": 5,
                        "http_path": "/health",
                        "healthy": {"interval": 10, "successes": 2},
                        "unhealthy": {"http_failures": 3}
                    }
                }

        Returns:
            Check: Pydantic Check model for APISIX
        """
        active_data = checks_data.get("active")
        passive_data = checks_data.get("passive")

        active_check = None
        passive_check = None

        if active_data:
            # Convert nested healthy/unhealthy
            healthy = None
            unhealthy = None

            if active_data.get("healthy"):
                healthy = ActiveHealthy(**active_data["healthy"])

            if active_data.get("unhealthy"):
                unhealthy = ActiveUnhealthy(**active_data["unhealthy"])

            # Create ActiveCheck with converted nested models
            active_check = ActiveCheck(
                type=CheckActiveTypeEnum(active_data.get("type", "http")),
                timeout=active_data.get("timeout"),
                concurrency=active_data.get("concurrency"),
                http_path=active_data.get("http_path"),
                host=active_data.get("host"),
                port=active_data.get("port"),
                https_verify_certificate=active_data.get("https_verify_certificate"),
                req_headers=active_data.get("req_headers"),
                healthy=healthy,
                unhealthy=unhealthy,
            )

        if passive_data:
            healthy = None
            unhealthy = None

            if passive_data.get("healthy"):
                healthy = PassiveHealthy(**passive_data["healthy"])

            if passive_data.get("unhealthy"):
                unhealthy = PassiveUnhealthy(**passive_data["unhealthy"])

            passive_check = PassiveCheck(
                type=CheckPassiveTypeEnum(passive_data.get("type", "http")),
                healthy=healthy,
                unhealthy=unhealthy,
            )

        # This will validate that at least one is set
        return Check(active=active_check, passive=passive_check)
