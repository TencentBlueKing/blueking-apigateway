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
from typing import List, Union

from django.conf import settings
from django.utils.encoding import force_bytes, force_str

from apigateway.common.constants import DEFAULT_BACKEND_HOST_FOR_MISSING
from apigateway.controller.models.base import Labels, Node, Plugin, Service, Timeout, Upstream
from apigateway.controller.models.constants import UpstreamSchemeEnum, UpstreamTypeEnum
from apigateway.controller.release_data.release_data import ReleaseData
from apigateway.core.models import Backend

from .base import BaseConvertor
from .utils import UrlInfo


class ServiceConvertor(BaseConvertor):
    # TODO: publish_id into labels of k8s => 需要确认
    #       确认新的 operator labels 怎么处理的？
    # labels["publish_id"] = str(self._publish_id)
    def __init__(self, release_data: ReleaseData, publish_id: Union[int, None] = None):
        super().__init__(release_data)
        self._publish_id = publish_id

    def convert(self) -> List[Service]:
        # FIXME: merge the stage + service here
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

        services: List[Service] = []
        # FIXME: 这里有没有环境变量渲染？

        for backend_id, backend_config in backend_configs.items():
            timeout = backend_config.get("timeout", 60)
            upstream = Upstream(
                type=UpstreamTypeEnum.ROUNDROBIN.value,
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
                    upstream.scheme = UpstreamSchemeEnum(url_info.scheme).value
                except ValueError:
                    raise ValueError(
                        f"scheme {url_info.scheme!r} of host {node['host']!r} is not a valid UpstreamSchemeEnum"
                    )

                upstream.nodes.append(Node(host=url_info.domain, port=url_info.port, weight=node.get("weight", 1)))

            # FIXME: move gateway/stage basic info into baseConvertor?
            stage_name = self._release_data.stage.name
            stage_id = self._release_data.stage.pk
            stage_description = self._release_data.stage.description

            backend = Backend.objects.get(id=backend_id)
            backend_name = backend.name
            backend_description = backend.description

            description = f"{stage_name}/{stage_id}"
            if stage_description:
                description += f": {stage_description[:32]}"
            description += f" (backend={backend_name}"
            if backend_description:
                description += f": {backend_description[:32]}"
            description += ")"

            # currently, only add one plugin for service of per backend
            # other plugins are shared by stage, they will be merged on operator
            plugins = [
                Plugin(
                    name="bk-backend-context",
                    config={
                        "bk_backend_id": backend_id,
                        "bk_backend_name": backend_name,
                    },
                ),
            ]
            stage_plugins = self._build_stage_plugins()
            plugins.extend(stage_plugins)

            # stage_name max length is 20, stage_id 6, backend_id is 4, other 10
            # total max length is 64, so the buffer is 24 ( stage_id length + backend_id length)
            # TODO: build the labels for every resource
            labels = Labels(
                gateway=self._release_data.gateway.name,
                stage=stage_name,
                publish_id=self._publish_id,
                # FIXME: add backend_id here?
            )
            services.append(
                Service(
                    # the previous id is: {gateway_name}.{stage_name}.{stage_id}-{backend_id}
                    # 30+1+20+1+ x + 1 + y = 53 + x + y, so x + y <= 11 (almost no buffer)
                    # so we should make a new id here?
                    # example: bk-apigateway-inner.prod.stage-6-backend-7
                    id=f"s-{stage_id}-b-{backend_id}",
                    # example: bk-apigateway-inner-prod-s-6-b-7
                    name=f"_stage_service_{stage_name}_{backend_id}",
                    desc=description,
                    labels=labels,
                    plugins=plugins,
                    upstream=upstream,
                    # metadata=self._common_metadata(
                    #     f"s-{stage_id}-b-{backend_id}",
                    #     labels={
                    #         "service-type": "stage-backend",
                    #         "backend-id": str(backend_id),
                    #     },
                    # ),
                    # spec=BkGatewayServiceSpec(
                    #     name=f"_stage_service_{stage_name}_{backend_id}",
                    #     id=f"stage-{stage_id}-backend-{backend_id}",
                    # ),
                )
            )

        return services

    # def stage_convert(self) -> BkGatewayStage:
    #     # FIXME: 如何处理 http/https 协议
    #     # FIXME: 环境变量渲染是不是 service 也有？
    #     http_info = MicroGatewayHTTPInfo.from_micro_gateway_config(self._micro_gateway.config)
    #     url_info = UrlInfo(http_info.http_url)
    #     path_prefix = url_info.path

    #     return BkGatewayStage(
    #         metadata=self._common_metadata(self._release_data.stage.name),
    #         spec=BkGatewayStageSpec(
    #             name=self._release_data.stage.name,
    #             description=self._release_data.stage.description,
    #             vars=self._release_data.stage.vars,
    #             path_prefix=path_prefix,
    #         ),
    #     )

    def _build_service_plugins(self) -> List[Plugin]:
        plugins = self._get_stage_default_plugins()
        plugins.extend(self._get_stage_binding_plugins())
        plugins.extend(self._get_stage_extra_plugins())

        return plugins

    def _get_stage_default_plugins(self) -> List[Plugin]:
        """Get the default plugins for stage, which is shared by all resources in the stage"""
        default_plugins = [
            # 2024-08-19 disable the bk-opentelemetry plugin, we should let each gateway set their own opentelemetry
            # Plugin(name="bk-opentelemetry"),
            Plugin(name="prometheus"),
            Plugin(name="bk-real-ip"),
            Plugin(name="bk-auth-validate"),
            Plugin(name="bk-auth-verify"),
            Plugin(name="bk-break-recursive-call"),
            Plugin(name="bk-delete-sensitive"),
            Plugin(name="bk-log-context"),
            Plugin(name="bk-delete-cookie"),
            Plugin(name="bk-error-wrapper"),
            Plugin(name="bk-jwt"),
            Plugin(name="bk-request-id"),
            Plugin(name="bk-response-check"),
            Plugin(name="bk-permission"),
            Plugin(name="bk-debug"),
            Plugin(
                name="file-logger",
                config={
                    "path": "logs/access.log",
                },
            ),
            Plugin(
                name="bk-stage-context",
                config={
                    "bk_gateway_name": self._release_data.gateway.name,
                    "bk_gateway_id": self._release_data.gateway.pk,
                    "bk_stage_name": self._release_data.stage.name,
                    "jwt_private_key": force_str(base64.b64encode(force_bytes(self._release_data.jwt_private_key))),
                    "bk_api_auth": self._release_data.gateway_auth_config,
                },
            ),
        ]

        if settings.GATEWAY_CONCURRENCY_LIMIT_ENABLED:
            default_plugins.append(Plugin(name="bk-concurrency-limit"))

        # 多租户模式
        if settings.ENABLE_MULTI_TENANT_MODE:
            default_plugins.extend(
                [
                    Plugin(name="bk-tenant-verify"),
                    Plugin(
                        name="bk-tenant-validate",
                        config={
                            "tenant_mode": self._release_data.gateway.tenant_mode,
                            "tenant_id": self._release_data.gateway.tenant_id,
                        },
                    ),
                ]
            )
        else:
            default_plugins.append(Plugin(name="bk-default-tenant"))

        return default_plugins

    def _get_stage_binding_plugins(self) -> List[Plugin]:
        return [
            Plugin(name=plugin_data.name, config=plugin_data.config)
            for plugin_data in self._release_data.get_stage_plugins()
        ]

    def _get_stage_extra_plugins(self) -> List[Plugin]:
        gateway_name = self._release_data.gateway.name
        if gateway_name in settings.LEGACY_INVALID_PARAMS_GATEWAY_NAMES:
            return [Plugin(name="bk-legacy-invalid-params")]
        return []
