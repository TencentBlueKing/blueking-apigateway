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
from typing import ClassVar, Optional

from pydantic import Field

from apigateway.controller.crds.constants import (
    ResourceProtocolEnum,
)
from apigateway.controller.crds.v1beta1.models.base import (
    GatewayCustomResourceSpec,
    Upstream,
)


class BkGatewayResourceSpec(GatewayCustomResourceSpec):
    kind: ClassVar[str] = "BkGatewayResource"

    protocol: ResourceProtocolEnum = Field(default=ResourceProtocolEnum.HTTP, description="协议")
    # is_public: bool = Field(default=False, alias="isPublic", description="是否公开")
    # allow_apply_permission: bool = Field(default=False, alias="allowApplyPermission", description="是否允许申请权限")

    # NOTE: make default None, otherwise would generate an empty upstream for route
    # upstream: Optional[Upstream] = Field(default_factory=Upstream, description="上游配置")
    upstream: Optional[Upstream] = Field(default=None, description="上游配置")
    # rewrite: ResourceRewrite = Field(default_factory=ResourceRewrite, description="请求重写")
