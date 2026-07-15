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
"""Define which user-bound plugins are compatible with each resource kind."""

from __future__ import annotations

from typing import TYPE_CHECKING

from apigateway.core.constants import ResourceKindEnum

if TYPE_CHECKING:
    from collections.abc import Iterable

COMMON_USER_BINDABLE_PLUGIN_TYPE_CODES = frozenset(
    {
        "bk-cors",
        "bk-rate-limit",
        "bk-ip-restriction",
        "request-validation",
        "bk-request-body-limit",
        "bk-user-restriction",
        "bk-access-token-source",
        "bk-username-required",
        "bk-oauth2-protected-resource",
        "bk-oauth2-verify",
        "bk-oauth2-audience-validate",
        "uri-blocker",
    }
)
AI_ONLY_USER_BINDABLE_PLUGIN_TYPE_CODES = frozenset({"ai-rate-limiting"})
CONTROLLER_MANAGED_PLUGIN_TYPE_CODES = frozenset({"ai-proxy", "ai-proxy-multi"})


def is_plugin_allowed_for_kind(plugin_type_code: str, kind: str) -> bool:
    if plugin_type_code in CONTROLLER_MANAGED_PLUGIN_TYPE_CODES:
        return False

    if kind == ResourceKindEnum.AI.value:
        return plugin_type_code in COMMON_USER_BINDABLE_PLUGIN_TYPE_CODES | AI_ONLY_USER_BINDABLE_PLUGIN_TYPE_CODES

    if kind == ResourceKindEnum.STANDARD.value:
        return plugin_type_code not in AI_ONLY_USER_BINDABLE_PLUGIN_TYPE_CODES

    raise ValueError(f"unsupported kind: {kind}")


def get_incompatible_plugin_type_codes(plugin_type_codes: Iterable[str], kind: str) -> list[str]:
    return [code for code in plugin_type_codes if not is_plugin_allowed_for_kind(code, kind)]
