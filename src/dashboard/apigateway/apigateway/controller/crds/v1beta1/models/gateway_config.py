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
from typing import ClassVar, List

from pydantic import Field

from apigateway.controller.crds.base import KubernetesModel
from apigateway.controller.crds.v1beta1.models.base import GatewayCustomResource, GatewayCustomResourceSpec


class ConfigControllerAuth(KubernetesModel):
    secret: str = Field(default="", description="jwt secret key", helm_value=True, helm_value_default="")


class ConfigController(KubernetesModel):
    base_path: str = Field(
        default="",
        alias="basePath",
        description="EdgeController server base path",
        helm_value=True,
        helm_value_default="/bk-apigateway/prod/api/v1/edge-controller/",
    )
    endpoints: List[str] = Field(
        default_factory=list,
        description="EdgeController server endpoints",
        helm_value=True,
        helm_value_default=["http://bkapi.example.com"],
    )
    jwt_auth: ConfigControllerAuth = Field(
        default_factory=ConfigControllerAuth,
        alias="jwtAuth",
        description="jwt 认证配置",
    )


class BkGatewayConfigSpec(GatewayCustomResourceSpec):
    instance_id: str = Field(default=None, alias="instanceID", helm_value=True, description="微网关实例 ID")
    controller: ConfigController = Field(default_factory=ConfigController, description="edge controller 配置")


class BkGatewayConfig(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayConfig"

    spec: BkGatewayConfigSpec
