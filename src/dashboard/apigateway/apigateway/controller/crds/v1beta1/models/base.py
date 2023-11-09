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
from typing import Any, Dict, List, Optional

from pydantic import Field

from apigateway.controller.crds.base import CustomResourceSpec, KubernetesModel, KubernetesResource
from apigateway.controller.crds.constants import (
    UpstreamCheckActiveTypeEnum,
    UpstreamHashOnEnum,
    UpstreamPassHostEnum,
    UpstreamSchemeEnum,
    UpstreamTypeEnum,
)


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


class PluginConfig(KubernetesModel):
    name: str = Field(default="", description="名称")
    config: Dict[str, Any] = Field(default_factory=dict, description="配置，以具体插件定义为准")


class TLSReference(KubernetesModel):
    gateway_tls_secret_ref: str = Field(default="", alias="gatewayTLSSecretRef", description="证书 Secret 名称")


class TimeoutConfig(KubernetesModel):
    connect: int = Field(default_factory=int, helm_value=True, description="连接超时，单位：秒")
    read: int = Field(default_factory=int, helm_value=True, description="接收超时，单位：秒")
    send: int = Field(default_factory=int, helm_value=True, description="发送超时，单位：秒")

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def default_timeout(cls):
        return cls(connect=30, read=30, write=30)


class UpstreamNode(KubernetesModel):
    host: str = Field(default="", description="主机地址")
    port: int = Field(default=0, description="端口")
    weight: int = Field(default=1, description="权重")
    priority: int = Field(default=1, description="优先级")


class UpstreamPassiveCheckHealthy(KubernetesModel):
    http_statuses: Optional[List[str]] = Field(
        default=None, alias="httpStatuses", description="健康节点的 HTTP 状态码"
    )
    successes: Optional[int] = Field(default=None, description="确定节点健康的次数")


class UpstreamActiveCheckHealthy(UpstreamPassiveCheckHealthy):
    interval: Optional[int] = Field(default=None, description="检查间隔")


class UpstreamPassiveCheckUnhealthy(KubernetesModel):
    http_statuses: Optional[List[str]] = Field(
        default=None, alias="httpStatuses", description="非健康节点的 HTTP 状态码"
    )
    http_failures: Optional[int] = Field(default=None, alias="httpFailures", description="非健康节点的 HTTP 失败次数")
    tcp_failures: Optional[int] = Field(default=None, alias="tcpFailures", description="非健康节点的 TCP 失败次数")
    timeouts: Optional[int] = Field(default=None, description="非健康节点的超时次数")


class UpstreamActiveCheckUnhealthy(UpstreamPassiveCheckUnhealthy):
    interval: Optional[int] = Field(default=None, description="检查间隔")


class UpstreamActiveCheck(KubernetesModel):
    type: UpstreamCheckActiveTypeEnum = Field(default=UpstreamCheckActiveTypeEnum.HTTP, description="主动检查的类型")
    timeout: Optional[int] = Field(default=None, description="主动检查的超时时间")
    concurrency: Optional[int] = Field(default=None, description="主动检查时同时检查的目标数")
    http_path: Optional[str] = Field(default=None, alias="httpPath", description="主动检查的 HTTP 请求路径")
    healthy: Optional[UpstreamActiveCheckHealthy] = Field(default=None, description="健康条件")
    unhealthy: Optional[UpstreamActiveCheckUnhealthy] = Field(default=None, description="非健康条件")


class UpstreamPassiveCheck(KubernetesModel):
    healthy: Optional[UpstreamPassiveCheckHealthy] = Field(default=None, description="健康条件")
    unhealthy: Optional[UpstreamPassiveCheckUnhealthy] = Field(default=None, description="非健康条件")


class UpstreamCheck(KubernetesModel):
    active: Optional[UpstreamActiveCheck] = Field(default=None, description="主动检查")
    passive: Optional[UpstreamPassiveCheck] = Field(default=None, description="被动检查")


class Upstream(KubernetesModel):
    type: UpstreamTypeEnum = Field(default=UpstreamTypeEnum.ROUNDROBIN, description="负载均衡方式")
    hash_on: Optional[UpstreamHashOnEnum] = Field(
        default=None, alias="hashOn", description="负载均衡方式为 chash 时使用"
    )
    key: Optional[str] = Field(default=None, alias="key", description="负载均衡方式为 chash 时进行 hash 的 key")
    checks: Optional[UpstreamCheck] = Field(default=None, description="健康检查")
    scheme: Optional[UpstreamSchemeEnum] = Field(default=UpstreamSchemeEnum.HTTP, description="请求协议")
    retries: Optional[int] = Field(default=None, description="重试次数")
    retry_timeout: Optional[int] = Field(default=None, alias="retryTimeout", description="重试超时")
    pass_host: UpstreamPassHostEnum = Field(
        default=UpstreamPassHostEnum.NODE, alias="passHost", description="请求发给上游时的 host"
    )
    upstream_host: Optional[str] = Field(
        default=None, alias="upstreamHost", helm_value=True, description="指定上游请求的 host"
    )
    tls_enable: Optional[bool] = Field(
        default=False, alias="tlsEnable", helm_value=True, description="是否开启 TLS 双向认证"
    )
    #  tls: Optional[TLSReference] = Field(default=None, description="TLS 证书引用")
    external_discovery_type: Optional[str] = Field(
        default=None, alias="externalDiscoveryType", description="外部发现类型"
    )
    external_discovery_config: Optional[Dict[str, Any]] = Field(
        default=None, alias="externalDiscoveryConfig", description="外部服务发现配置"
    )
    discovery_type: Optional[str] = Field(default=None, alias="discoveryType", description="服务发现方式")
    service_name: Optional[str] = Field(
        default=None,
        alias="serviceName",
        description="后端服务名",
        helm_value=True,
        helm_value_default="example.service.svc",
    )
    nodes: List[UpstreamNode] = Field(default_factory=list, description="上游节点", helm_value=True)
    timeout: Optional[TimeoutConfig] = Field(default=None, description="超时配置")
