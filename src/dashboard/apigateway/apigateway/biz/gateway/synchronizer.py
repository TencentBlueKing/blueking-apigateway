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
from typing import Dict, List, Optional

from django.conf import settings
from pydantic import BaseModel, Field, validator

from apigateway.core.constants import GatewayTypeEnum
from apigateway.core.models import Gateway

from .gateway import GatewayHandler


class GatewaySyncData(BaseModel):
    name: str = Field(...)
    description: str = Field(default="")
    description_en: Optional[str] = Field(default=None)
    maintainers: List[str] = Field(default_factory=list)
    status: int = Field(...)
    is_public: bool = Field(default=False)
    gateway_type: Optional[GatewayTypeEnum] = Field(default=None)
    user_config: Optional[Dict] = Field(default=None)

    @validator("gateway_type")
    def validate_gateway_type(self, v):
        return GatewayTypeEnum(v) if isinstance(v, int) else v


class GatewaySynchronizer:
    def __init__(
        self,
        gateway: Optional[Gateway],
        gateway_data: GatewaySyncData,
        bk_app_code: str = "",
        username: str = "",
    ):
        self.gateway = gateway
        self.gateway_data = gateway_data
        self.bk_app_code = bk_app_code
        self.username = username

    def sync(self) -> Gateway:
        if not self.gateway:
            self._create_gateway()
        else:
            self._update_gateway()

        return self.gateway

    def _create_gateway(self):
        # 1. save gateway
        self.gateway = gateway = Gateway(
            name=self.gateway_data.name,
            description=self.gateway_data.description,
            description_en=self.gateway_data.description_en,
            maintainers=self.gateway_data.maintainers,
            status=self.gateway_data.status,
            is_public=self.gateway_data.is_public,
            created_by=self.username,
            updated_by=self.username,
        )
        gateway.save()

        # 2. save related data
        GatewayHandler.save_related_data(
            gateway=gateway,
            user_auth_type=settings.DEFAULT_USER_AUTH_TYPE,
            username=self.username,
            related_app_code=self.bk_app_code,
            user_config=self.gateway_data.user_config,
            unfiltered_sensitive_keys=self._get_gateway_unfiltered_sensitive_keys(gateway.name),
            api_type=self.gateway_data.gateway_type,
        )

    def _update_gateway(self):
        gateway = self.gateway

        # 1. update gateway
        gateway.description = self.gateway_data.description
        gateway.description_en = self.gateway_data.description_en
        # 更新网关时，仅新增网关管理员，不删除，以防止删除已更新的管理员数据
        gateway.maintainers = sorted(set(self.gateway_data.maintainers + gateway.maintainers))
        gateway.is_public = self.gateway_data.is_public
        gateway.updated_by = self.username
        gateway.save()

        # 2. update auth config
        GatewayHandler.save_auth_config(
            gateway.id,
            user_conf=self.gateway_data.user_config,
            unfiltered_sensitive_keys=self._get_gateway_unfiltered_sensitive_keys(gateway.name),
            api_type=self.gateway_data.gateway_type,
        )

    def _get_gateway_unfiltered_sensitive_keys(self, gateway_name: str) -> Optional[List[str]]:
        gateway_auth_configs = getattr(settings, "SPECIAL_GATEWAY_AUTH_CONFIGS", None) or {}
        return gateway_auth_configs.get(gateway_name, {}).get("unfiltered_sensitive_keys")
