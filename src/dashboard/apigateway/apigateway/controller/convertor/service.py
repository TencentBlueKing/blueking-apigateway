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

import base64
from typing import TYPE_CHECKING, Any, Dict, List, Optional

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
from apigateway.controller.uri_render import URIRender
from apigateway.core.constants import BackendKindEnum, LoadBalanceTypeEnum

from .base import GatewayResourceConvertor
from .constants import LABEL_KEY_BACKEND_ID
from .utils import UrlInfo, truncate_string

if TYPE_CHECKING:
    from apigateway.controller.release_data import ReleaseData, StageBackendConfig


def _build_ai_log_format() -> Dict[str, str]:
    return {
        "proto": "$server_protocol",
        "method": "$request_method",
        "http_host": "$host",
        "http_path": "$uri",
        "app_code": "$bk_app_code",
        "client_ip": "$remote_addr",
        "request_id": "$bk_request_id",
        "x_request_id": "$x_request_id",
        "request_duration": "$bk_log_request_duration",
        "bk_username": "$bk_username",
        "bk_tenant_id": "$bk_tenant_id",
        "gateway_id": "$bk_gateway_id",
        "gateway_name": "$bk_gateway_name",
        "resource_id": "$bk_resource_id",
        "resource_name": "$bk_resource_name",
        "stage": "$bk_stage_name",
        "backend_name": "$bk_backend_name",
        "response_size": "$body_bytes_sent",
        "status": "$status",
        "code_name": "$bk_apigw_error_code_name",
        "error": "$bk_apigw_error_message",
        "proxy_error": "$proxy_error",
        "timestamp": "$bk_log_request_timestamp",
        "traceparent": "$http_traceparent",
    }


def _build_ai_proxy_plugin(config: Dict[str, Any]) -> Plugin:
    instance = config["instances"][0]
    plugin_config: Dict[str, Any] = {
        "provider": instance["provider"],
        "auth": instance.get("auth", {}),
        "options": instance["options"],
        "timeout": config.get("timeout", 30000),
        "ssl_verify": True,
        "logging": {"summaries": True, "payloads": False},
    }
    if "override" in instance:
        plugin_config["override"] = instance["override"]
    return Plugin(**plugin_config)


class ServiceConvertor(GatewayResourceConvertor):
    def __init__(
        self,
        release_data: ReleaseData,
        publish_id: int,
        apisix_version: str,
        revoke_flag: Optional[bool] = False,
    ):
        super().__init__(release_data=release_data, publish_id=publish_id, apisix_version=apisix_version)
        self._revoke_flag = revoke_flag

    def convert(self) -> List[GatewayApisixModel]:  # noqa: C901, PLR0912
        # if revoke, we should not generate service, will delete the service from etcd
        if self._revoke_flag:
            return []

        # FIXME: should not generate service if the backend is not related to any resource
        backend_configs = self._release_data.stage_backend_configs
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

        for backend_id, stage_backend_config in backend_configs.items():
            if stage_backend_config.backend_kind == BackendKindEnum.AI.value:
                services.append(self._build_ai_service(stage_backend_config))
                continue
            if stage_backend_config.backend_kind != BackendKindEnum.STANDARD.value:
                raise ValueError(f"unsupported backend kind: {stage_backend_config.backend_kind}")

            backend_config = stage_backend_config.config
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
            backend_name = stage_backend_config.backend_name

            # currently, only add one plugin for service of per backend
            # other plugins are shared by stage, they will be merged on operator
            plugins: Dict[str, Plugin] = {
                "bk-backend-context": Plugin(bk_backend_id=backend_id, bk_backend_name=backend_name),
            }
            service_plugins = self._build_service_plugins(stage_backend_config.backend_kind)
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
                    # example: bk-apigateway.prod.6-7
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
                    labels=labels,
                    plugins=plugins,
                    upstream=upstream,
                )
            )

        return services

    def _build_ai_service(self, backend_config: StageBackendConfig) -> Service:
        plugins = self._build_service_plugins(backend_config.backend_kind)
        plugins["bk-backend-context"] = Plugin(
            bk_backend_id=backend_config.backend_id,
            bk_backend_name=backend_config.backend_name,
        )
        plugins["ai-proxy"] = _build_ai_proxy_plugin(backend_config.config)
        labels = self.get_labels()
        labels.add_label(LABEL_KEY_BACKEND_ID, str(backend_config.backend_id))

        return Service(
            id=f"{self.gateway_name}.{self.stage_name[:10]}.{self.stage_id}-{backend_config.backend_id}",
            name=truncate_string(
                f"{self.gateway_name}.{self.stage_name}.{backend_config.backend_name}",
                100,
            ),
            labels=labels,
            plugins=plugins,
            # AI Services are upstream-less; ai-proxy resolves the provider upstream.
            upstream=None,
        )

    def _build_service_plugins(self, backend_kind: str) -> Dict[str, Plugin]:
        plugins = self._get_common_default_plugins()
        plugins.update(self._get_kind_default_plugins(backend_kind))
        plugins.update(self._get_stage_binding_plugins())
        plugins.update(self._get_stage_extra_plugins(backend_kind))
        return plugins

    def _get_common_default_plugins(self) -> Dict[str, Plugin]:
        """Get the default plugins shared by all Services in the stage."""
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

    def _get_kind_default_plugins(self, backend_kind: str) -> Dict[str, Plugin]:
        if backend_kind == BackendKindEnum.AI.value:
            return {"file-logger": Plugin(path="logs/access.log", log_format=_build_ai_log_format())}
        if backend_kind == BackendKindEnum.STANDARD.value:
            return {"file-logger": Plugin(path="logs/access.log")}
        raise ValueError(f"unsupported backend kind: {backend_kind}")

    def _get_stage_binding_plugins(self) -> Dict[str, Plugin]:
        return {
            plugin_data.name: Plugin(**plugin_data.config) for plugin_data in self._release_data.get_stage_plugins()
        }

    def _get_stage_extra_plugins(self, backend_kind: str) -> Dict[str, Plugin]:
        if (
            backend_kind == BackendKindEnum.STANDARD.value
            and self.gateway_name in settings.LEGACY_INVALID_PARAMS_GATEWAY_NAMES
        ):
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
                https_verify_certificate=active_data.get("https_verify_certificate"),
                # NOTE: 暂时不支持，后续再支持
                # host=active_data.get("host"),
                # port=active_data.get("port"),
                # req_headers=active_data.get("req_headers"),
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
