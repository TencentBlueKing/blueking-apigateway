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
from typing import Optional

from pydantic import Field

from apigateway.controller.crds.base import CustomResourceSpec, KubernetesModel, KubernetesResource


class GatewayCustomResourceSpec(CustomResourceSpec):
    name: str = Field(default="", description="名称")
    description: Optional[str] = Field(default="", alias="desc", helm_value=True, description="描述")


class GatewayCustomResource(KubernetesResource):
    @property
    def key(self) -> str:
        """资源的索引名称，在保证唯一性的前提下，兼顾可读性，含义不做保证"""
        return self.metadata.name

    @property
    def name(self) -> str:
        """资源真实名称"""
        return self.spec.name  # type: ignore

    @property
    def gateway(self) -> str:
        """所属网关名称"""
        return self.metadata.get_label("gateway", default="")

    @property
    def stage(self) -> str:
        """所属环境名称"""
        return self.metadata.get_label("stage", default="")


class Upstream(KubernetesModel):
    upstream_host: Optional[str] = Field(
        default=None, alias="upstreamHost", helm_value=True, description="指定上游请求的 host"
    )
    tls_enable: Optional[bool] = Field(
        default=False, alias="tlsEnable", helm_value=True, description="是否开启 TLS 双向认证"
    )
