#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
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

from typing import Dict, List

from django.utils.functional import cached_property

from apigateway.common.factories import SchemaFactory
from apigateway.core.constants import ContextScopeTypeEnum, ContextTypeEnum, ResourceAuthTypeEnum
from apigateway.core.models import Resource

from .context import BaseContext

RESOURCE_OAUTH2_CLIENT_FIELDS = (
    "oauth2_public_client_enabled",
    "oauth2_personal_client_enabled",
)
# 只读推导字段：只出现在接口输出中，写入时忽略，不进入存储与版本快照
RESOURCE_AUTH_DERIVED_FIELDS = (
    "auth_type",
    "oauth2_app_delegated_enabled",
)


def derive_resource_auth_type(config: dict) -> str:
    if config.get("auth_verified_required", True):
        return ResourceAuthTypeEnum.USER.value
    if config.get("app_verified_required", True):
        return ResourceAuthTypeEnum.APP.value
    return ResourceAuthTypeEnum.NONE.value


def with_resource_auth_derived_fields(config: dict) -> dict:
    """Return a copy of the auth config with the read-only fields derived from the legacy fields."""
    result = dict(config)
    result["auth_type"] = derive_resource_auth_type(config)
    result["oauth2_app_delegated_enabled"] = bool(
        config.get("auth_verified_required", True) and config.get("app_verified_required", True)
    )
    return result


def build_resource_auth_config(resource: Resource, context_config: dict) -> dict:
    config = dict(context_config)
    for field_name in RESOURCE_OAUTH2_CLIENT_FIELDS:
        config[field_name] = getattr(resource, field_name)
    return config


def strip_resource_oauth2_client_config(config: dict) -> dict:
    context_config = dict(config)
    for field_name in RESOURCE_OAUTH2_CLIENT_FIELDS:
        context_config.pop(field_name, None)
    return context_config


class ResourceAuthContext(BaseContext):
    scope_type = ContextScopeTypeEnum.RESOURCE.value
    type = ContextTypeEnum.RESOURCE_AUTH.value

    @cached_property
    def schema(self):
        return SchemaFactory().get_context_resource_bkauth_schema()

    def get_config_for_resource(self, resource: Resource) -> dict:
        return build_resource_auth_config(resource, self.get_config(resource.id))

    def get_resource_id_to_auth_config(self, resource_ids: List[int]) -> Dict[int, dict]:
        context_config_map = {context.scope_id: context.config for context in self.filter_contexts(resource_ids)}
        return {
            resource.id: build_resource_auth_config(resource, context_config_map.get(resource.id, {}))
            for resource in Resource.objects.filter(id__in=resource_ids)
        }
