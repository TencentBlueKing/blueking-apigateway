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
from pydantic import BaseModel, Field, field_validator

from apigateway.core.constants import GatewayTypeEnum
from apigateway.core.models import Gateway

from .gateway import GatewayHandler


class GatewayData(BaseModel):
    name: str = Field(...)
    description: str = Field(default="")
    description_en: Optional[str] = Field(default=None)
    maintainers: List[str] = Field(default_factory=list)
    status: int = Field(...)
    is_public: bool = Field(default=False)
    gateway_type: Optional[GatewayTypeEnum] = Field(default=None)
    user_config: Optional[Dict] = Field(default=None)
    # allow_auth_from_params/allow_delete_sensitive_params 默认值 None，即默认不修改此配置，
    # 上层如需修改，需明确指定配置值
    allow_auth_from_params: Optional[bool] = Field(default=None)
    allow_delete_sensitive_params: Optional[bool] = Field(default=None)

    tenant_mode: Optional[str] = Field(default=None)
    tenant_id: Optional[str] = Field(default=None)

    @field_validator("gateway_type")
    def validate_gateway_type(cls, v):  # noqa: N805
        return GatewayTypeEnum(v) if isinstance(v, int) else v


class GatewaySaver:
    def __init__(
        self,
        id: Optional[int],
        data: GatewayData,
        bk_app_code: str = "",
        username: str = "",
    ):
        self.bk_app_code = bk_app_code
        self.username = username

        self._gateway = self._get_gateway(id)
        self._gateway_data = data

    def _get_gateway(self, gateway_id: Optional[int]) -> Optional[Gateway]:
        if gateway_id:
            return Gateway.objects.get(id=gateway_id)

        return None

    def save(self) -> Gateway:
        # 网关为 None，则新建网关；非 None，则更新网关
        if not self._gateway:
            self._create_gateway()
        else:
            self._update_gateway()

        assert self._gateway

        return self._gateway

    def _create_gateway(self):
        # 1. save gateway
        self._gateway = gateway = Gateway(
            name=self._gateway_data.name,
            description=self._gateway_data.description,
            description_en=self._gateway_data.description_en,
            maintainers=self._gateway_data.maintainers,
            status=self._gateway_data.status,
            is_public=self._gateway_data.is_public,
            tenant_mode=self._gateway_data.tenant_mode,
            tenant_id=self._gateway_data.tenant_id,
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
            user_config=self._gateway_data.user_config,
            unfiltered_sensitive_keys=self._get_gateway_unfiltered_sensitive_keys(gateway.name),
            api_type=self._gateway_data.gateway_type,
            allow_auth_from_params=self._gateway_data.allow_auth_from_params,
            allow_delete_sensitive_params=self._gateway_data.allow_delete_sensitive_params,
        )

    def _update_gateway(self):
        gateway = self._gateway

        # 1. update gateway
        gateway.description = self._gateway_data.description
        gateway.description_en = self._gateway_data.description_en
        # 更新网关时，仅新增网关管理员，不删除，以防止删除已更新的管理员数据
        gateway.maintainers = sorted(set(self._gateway_data.maintainers + gateway.maintainers))
        gateway.is_public = self._gateway_data.is_public
        gateway.updated_by = self.username
        gateway.save()

        # 2. update auth config
        GatewayHandler.save_auth_config(
            gateway.id,
            user_conf=self._gateway_data.user_config,
            unfiltered_sensitive_keys=self._get_gateway_unfiltered_sensitive_keys(gateway.name),
            api_type=self._gateway_data.gateway_type,
            allow_auth_from_params=self._gateway_data.allow_auth_from_params,
            allow_delete_sensitive_params=self._gateway_data.allow_delete_sensitive_params,
        )

    def _get_gateway_unfiltered_sensitive_keys(self, gateway_name: str) -> Optional[List[str]]:
        gateway_auth_configs = getattr(settings, "SPECIAL_GATEWAY_AUTH_CONFIGS", None) or {}
        return gateway_auth_configs.get(gateway_name, {}).get("unfiltered_sensitive_keys")
