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
from dataclasses import dataclass
from typing import Any, Dict, List

from django.conf import settings
from django.utils.functional import cached_property

from apigateway.common.factories import SchemaFactory
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum, GatewayTypeEnum

from .context import BaseContext


@dataclass
class GatewayAuthConfig:
    gateway_type: int = GatewayTypeEnum.CLOUDS_API.value
    user_auth_type: str = settings.DEFAULT_USER_AUTH_TYPE
    allow_update_gateway_auth: bool = False


class GatewayAuthContext(BaseContext):
    scope_type = ContextScopeTypeEnum.GATEWAY.value
    type = ContextTypeEnum.GATEWAY_AUTH.value

    @cached_property
    def schema(self):
        return SchemaFactory().get_context_gateway_bkauth_schema()

    def get_gateway_id_to_auth_config(self, gateway_ids: List[int]) -> Dict[int, GatewayAuthConfig]:
        return {
            context.scope_id: self._get_auth_config(context.config) for context in self.filter_contexts(gateway_ids)
        }

    def get_auth_config(self, gateway_id: int) -> GatewayAuthConfig:
        config = super().get_config(gateway_id)
        return self._get_auth_config(config)

    def _get_auth_config(self, config: Dict[str, Any]) -> GatewayAuthConfig:
        return GatewayAuthConfig(
            gateway_type=config.get("api_type", GatewayTypeEnum.CLOUDS_API.value),
            user_auth_type=config.get("user_auth_type", settings.DEFAULT_USER_AUTH_TYPE),
            allow_update_gateway_auth=config.get("allow_update_api_auth", False),
        )
