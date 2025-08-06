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
from typing import List

from apigateway.controller.crds.constants import UpstreamSchemeEnum, UpstreamTypeEnum
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor, UrlInfo
from apigateway.controller.crds.v1beta1.models.base import TimeoutConfig, Upstream, UpstreamNode
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService, BkGatewayServiceSpec


class ServiceConvertor(BaseConvertor):
    def convert(self) -> List[BkGatewayService]:
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

        services: List[BkGatewayService] = []

        for backend_id, backend_config in backend_configs.items():
            timeout = backend_config.get("timeout", 60)
            upstream = Upstream(
                type=UpstreamTypeEnum.ROUNDROBIN,
                timeout=TimeoutConfig(
                    connect=timeout,
                    send=timeout,
                    read=timeout,
                ),
            )
            hosts = backend_config.get("hosts", [])
            for node in hosts:
                host = node["host"]
                # 如果 default 没有设置 host，则默认使用 0.0.0.0 来替代，避免 apisix 加载报错
                if host == "":
                    host = "your-backend-host"
                if "scheme" in node:
                    host = node["scheme"] + "://" + host
                url_info = UrlInfo(host)

                try:
                    upstream.scheme = UpstreamSchemeEnum(url_info.scheme)
                except ValueError:
                    raise ValueError(
                        f"scheme {url_info.scheme!r} of host {node['host']!r} is not a valid UpstreamSchemeEnum"
                    )

                upstream.nodes.append(
                    UpstreamNode(host=url_info.domain, port=url_info.port, weight=node.get("weight", 1))
                )

            stage_name = self._release_data.stage.name
            stage_id = self._release_data.stage.pk

            # stage_name max length is 20, stage_id 6, backend_id is 4, other 10
            # total max length is 64, so the buffer is 24 ( stage_id length + backend_id length)
            services.append(
                BkGatewayService(
                    metadata=self._common_metadata(
                        f"stage-{stage_name}-{stage_id}-b-{backend_id}",
                        labels={
                            "service-type": "stage-backend",
                            "backend-id": str(backend_id),
                        },
                    ),
                    spec=BkGatewayServiceSpec(
                        name=f"_stage_service_{stage_name}_{backend_id}",
                        id=f"stage-{stage_id}-backend-{backend_id}",
                        description=self._release_data.stage.description,
                        upstream=upstream,
                    ),
                )
            )

        return services
