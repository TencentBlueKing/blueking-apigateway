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
from typing import ClassVar, Dict, List

from pydantic import Field

from apigateway.controller.crds.v1beta1.models.base import (
    GatewayCustomResource,
    GatewayCustomResourceSpec,
    KubernetesModel,
    PluginConfig,
)


class StageRewrite(KubernetesModel):
    enabled: bool = Field(default=False, helm_value=True, description="是否启用")
    headers: Dict[str, str] = Field(default_factory=dict, helm_value=True, description="重写请求头")


class BkGatewayStageSpec(GatewayCustomResourceSpec):
    domain = Field(default="", description="访问域名", helm_value=True, helm_value_default="")
    path_prefix = Field(
        default="", description="访问路径前缀", helm_value=True, helm_value_default="/", alias="pathPrefix"
    )
    vars: Dict[str, str] = Field(default_factory=dict, description="环境变量", helm_value=True)
    rewrite: StageRewrite = Field(default_factory=StageRewrite, description="环境通用请求重写")
    plugins: List[PluginConfig] = Field(default_factory=list, description="插件配置", helm_value=True)


class BkGatewayStage(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayStage"
    spec: BkGatewayStageSpec
