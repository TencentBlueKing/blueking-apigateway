#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) Tencent. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
# https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
"""Define which plugins can be configured for a resource kind."""

from __future__ import annotations

from apigateway.apps.plugin.constants import PluginTypeCodeEnum
from apigateway.core.constants import ResourceKindEnum

AI_ONLY_PLUGIN_CODES = frozenset(
    {
        "ai-prompt-decorator",
        "ai-prompt-guard",
        "ai-rate-limiting",
    }
)

AI_RESOURCE_INCOMPATIBLE_PLUGIN_CODES = frozenset(
    {
        PluginTypeCodeEnum.API_BREAKER.value,
        PluginTypeCodeEnum.BK_HEADER_REWRITE.value,
        PluginTypeCodeEnum.BK_LEGACY_INVALID_PARAMS.value,
        PluginTypeCodeEnum.BK_QUERY_STRING_REWRITE.value,
        PluginTypeCodeEnum.BK_STATUS_REWRITE.value,
        PluginTypeCodeEnum.BK_TRAFFIC_LABEL.value,
        PluginTypeCodeEnum.PROXY_CACHE.value,
        PluginTypeCodeEnum.RESPONSE_REWRITE.value,
        PluginTypeCodeEnum.BK_MOCK.value,
        PluginTypeCodeEnum.REDIRECT.value,
        PluginTypeCodeEnum.FAULT_INJECTION.value,
    }
)


def is_plugin_compatible_with_resource_kind(plugin_code: str, resource_kind: str | None) -> bool:
    if plugin_code in AI_ONLY_PLUGIN_CODES:
        return resource_kind == ResourceKindEnum.AI.value

    if resource_kind == ResourceKindEnum.AI.value:
        return plugin_code not in AI_RESOURCE_INCOMPATIBLE_PLUGIN_CODES

    return True
