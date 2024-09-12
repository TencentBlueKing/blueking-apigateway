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
from typing import ClassVar, Dict, List, Optional

from pydantic import Field

from apigateway.controller.crds.constants import (
    HttpResourceMethodEnum,
    ResourceProtocolEnum,
    ResourceRewriteHeadersStrategyEnum,
)
from apigateway.controller.crds.v1beta1.models.base import (
    GatewayCustomResource,
    GatewayCustomResourceSpec,
    KubernetesModel,
    PluginConfig,
    TimeoutConfig,
    Upstream,
)


class ResourceRewrite(KubernetesModel):
    enabled: bool = Field(default=False, description="是否启用")
    method: Optional[str] = Field(default=None, description="重写请求方法")
    path: Optional[str] = Field(default=None, description="重写请求路径")
    headers: Dict[str, str] = Field(default_factory=dict, helm_value=True, description="重写请求头")
    stage_headers: ResourceRewriteHeadersStrategyEnum = Field(
        default_factory=lambda: ResourceRewriteHeadersStrategyEnum.APPEND,
        alias="stageHeaders",
        description="环境重写请求头合并策略",
    )
    service_headers: ResourceRewriteHeadersStrategyEnum = Field(
        default_factory=lambda: ResourceRewriteHeadersStrategyEnum.APPEND,
        alias="serviceHeaders",
        description="服务重写请求头合并策略",
    )


class BkGatewayResourceSpec(GatewayCustomResourceSpec):
    kind: ClassVar[str] = "BkGatewayResource"

    id: Optional[int] = Field(default=None, description="资源 ID")
    plugins: List[PluginConfig] = Field(default_factory=list, description="插件配置", helm_value=True)
    service: str = Field(default="", description="服务名称")
    protocol: ResourceProtocolEnum = Field(default=ResourceProtocolEnum.HTTP, description="协议")
    methods: List[HttpResourceMethodEnum] = Field(default_factory=list, description="请求方法")
    timeout: Optional[TimeoutConfig] = Field(default=None, description="超时配置")
    uri: str = Field(default="/", description="请求路径")
    match_subpath: bool = Field(default=False, alias="matchSubPath", description="是否匹配子路径")
    # is_public: bool = Field(default=False, alias="isPublic", description="是否公开")
    # allow_apply_permission: bool = Field(default=False, alias="allowApplyPermission", description="是否允许申请权限")
    upstream: Optional[Upstream] = Field(default_factory=Upstream, description="上游配置")
    rewrite: ResourceRewrite = Field(default_factory=ResourceRewrite, description="请求重写")


class BkGatewayResource(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayResource"
    spec: BkGatewayResourceSpec

    @property
    def resource(self) -> str:
        return self.get_label("resource", default="")
