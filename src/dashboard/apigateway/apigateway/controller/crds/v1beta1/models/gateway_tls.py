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


class TLSSecretStringData(KubernetesModel):
    ca: str = Field(default=None, alias="ca.crt", description="CA 证书", helm_value=True, helm_value_default="")
    crt: str = Field(default=None, alias="tls.crt", description="证书", helm_value=True, helm_value_default="")
    key: str = Field(default=None, alias="tls.key", description="私钥", helm_value=True, helm_value_default="")


class TLSSecret(GatewayCustomResource):
    kind: ClassVar[str] = "Secret"
    string_data: TLSSecretStringData = Field(alias="stringData", description="明文内容")


class BkGatewayTLSSpec(GatewayCustomResourceSpec):
    kind: ClassVar[str] = "BkGatewayTLS"

    snis: List[str] = Field(default_factory=list, description="SNI 名称列表", helm_value=True)
    gateway_tls_secret_ref: str = Field(
        default="",
        alias="gatewayTLSSecretRef",
        description="证书 Secret 名称",
        helm_value=True,
    )


class BkGatewayTLS(GatewayCustomResource):
    kind: ClassVar[str] = "BkGatewayTLS"
    spec: BkGatewayTLSSpec
