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
