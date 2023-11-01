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

from apigateway.controller.crds.v1beta1.models.base import (
    GatewayCustomResource,
    GatewayCustomResourceSpec,
    KubernetesModel,
    PluginConfig,
    Upstream,
)


class ServiceRewrite(KubernetesModel):
    enabled: bool = Field(default=False, description="是否启用")
    headers: Dict[str, str] = Field(default_factory=dict, description="重写请求头")


class BkGatewayServiceSpec(GatewayCustomResourceSpec):
    id: Optional[str] = Field(default=None, description="服务 UUID")
    upstream: Upstream = Field(default_factory=Upstream, description="上游配置")
    rewrite: ServiceRewrite = Field(default_factory=ServiceRewrite, description="服务通用请求重写")
    plugins: List[PluginConfig] = Field(default_factory=list, description="插件配置")


class BkGatewayService(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayService"
    spec: BkGatewayServiceSpec
