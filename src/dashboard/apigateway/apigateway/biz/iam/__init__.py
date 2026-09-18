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
from .auth import (
    clear_gateway_iam_auth_cache,
    is_iam_auth_active,
    is_iam_gateway_action_allowed,
)
from .authorization import (
    GatewayMemberAuthorization,
    GatewayMemberSnapshot,
    apply_gateway_member_snapshots_to_iam,
    build_gateway_authorization,
    build_gateway_member_snapshot,
    build_gateway_revoke_authorization,
    get_gateway_iam_system_operator,
)
from .model import GatewayIAMModelSyncer, GatewayIAMModelSyncResult
from .sync import (
    GatewayIAMAuthorization,
    GatewayIAMAuthorizationSynchronizer,
    GatewayIAMSyncItem,
    GatewayIAMSyncResult,
)

__all__ = [
    # constant
    # Enum
    # class
    "GatewayIAMAuthorization",
    "GatewayIAMAuthorizationSynchronizer",
    "GatewayIAMModelSyncer",
    "GatewayIAMModelSyncResult",
    "GatewayIAMSyncItem",
    "GatewayIAMSyncResult",
    "GatewayMemberAuthorization",
    # functions
    "apply_gateway_member_snapshots_to_iam",
    "build_gateway_authorization",
    "build_gateway_member_snapshot",
    "build_gateway_revoke_authorization",
    "clear_gateway_iam_auth_cache",
    "get_gateway_iam_system_operator",
    "is_iam_auth_active",
    "is_iam_gateway_action_allowed",
    # others
    "GatewayMemberSnapshot",
]
