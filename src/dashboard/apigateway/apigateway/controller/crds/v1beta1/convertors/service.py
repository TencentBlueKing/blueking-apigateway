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
from typing import List

from apigateway.controller.crds.constants import UpstreamSchemeEnum, UpstreamTypeEnum
from apigateway.controller.crds.v1beta1.convertors.base import BaseConvertor, UrlInfo
from apigateway.controller.crds.v1beta1.models.base import TimeoutConfig, Upstream, UpstreamNode
from apigateway.controller.crds.v1beta1.models.gateway_service import BkGatewayService, BkGatewayServiceSpec


class ServiceConvertor(BaseConvertor):
    def convert(self) -> List[BkGatewayService]:
        upstreams = self._release_data.stage_upstreams
        if not upstreams:
            return []

        timeout = self._release_data.stage_backend_config.get("timeout", 0)

        upstream = Upstream(
            type=UpstreamTypeEnum.ROUNDROBIN,
            timeout=TimeoutConfig(
                connect=timeout,
                send=timeout,
                read=timeout,
            ),
        )

        for node in upstreams.get("hosts", []):
            host = node["host"]
            ## 如果default没有设置host，则默认使用 0.0.0.0来替代，避免apisix加载报错
            if host == "":
                host = "0.0.0.0"
            if "scheme" in node:
                host = node["scheme"] + "://" + host
            url_info = UrlInfo(host)

            try:
                upstream.scheme = UpstreamSchemeEnum(url_info.scheme)
            except ValueError:
                raise ValueError(
                    f"scheme {url_info.scheme!r} of host {node['host']!r} is not a valid UpstreamSchemeEnum"
                )

            upstream.nodes.append(UpstreamNode(host=url_info.domain, port=url_info.port, weight=node.get("weight", 1)))

        return [
            BkGatewayService(
                metadata=self._common_metadata(
                    f"stage-{self._release_data.stage.name}-{self._release_data.stage.pk}",
                    labels={"service-type": "stage"},
                ),
                spec=BkGatewayServiceSpec(
                    name=f"_stage_service_{self._release_data.stage.name}",
                    id=f"stage-{self._release_data.stage.pk}",
                    description=self._release_data.stage.description,
                    upstream=upstream,
                ),
            )
        ]
