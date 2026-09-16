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
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Mapping

from django.conf import settings
from django.utils import timezone

from apigateway.apps.rbac.constants import GatewayResourceTypeEnum
from apigateway.components.bkiam import (
    AuthorizationPayload,
    RevokeAuthorizationPayload,
    add_authorization,
    chunked,
    revoke_authorization,
)

from .constants import GATEWAY_MEMBER_EXPIRE_DAYS

if TYPE_CHECKING:
    from collections.abc import Iterable

    from apigateway.apps.rbac.models import GatewayMember

logger = logging.getLogger(__name__)


def get_gateway_iam_system_operator() -> str:
    """Return the configured IAM system operator for background writes."""
    managers = settings.BK_IAM_V4_MANAGERS
    if not managers or any(not isinstance(manager, str) or not manager.strip() for manager in managers):
        raise ValueError("BK_IAM_V4_MANAGERS must contain at least one non-empty manager")
    return managers[0].strip()


@dataclass(frozen=True)
class GatewayMemberAuthorization:
    role: str
    expires: datetime | None


GatewayMemberSnapshot = Mapping[str, GatewayMemberAuthorization]


def build_gateway_authorization(
    username: str,
    role: str,
    gateway_id: int,
    expires: datetime | None,
    *,
    now: datetime | None = None,
) -> AuthorizationPayload:
    effective_expires = expires or (now or timezone.now()) + timedelta(days=GATEWAY_MEMBER_EXPIRE_DAYS)
    return {
        "subject": {"type": "user", "id": username},
        "role_id": role,
        "expired_at": int(effective_expires.timestamp()),
        "related_resource_type_id": GatewayResourceTypeEnum.GATEWAY.value,
        "resources": [{"type": GatewayResourceTypeEnum.GATEWAY.value, "id": str(gateway_id)}],
    }


def build_gateway_revoke_authorization(
    username: str,
    role: str,
    gateway_id: int,
) -> RevokeAuthorizationPayload:
    return {
        "subject": {"type": "user", "id": username},
        "role_id": role,
        "related_resource_type_id": GatewayResourceTypeEnum.GATEWAY.value,
        "resources": [{"type": GatewayResourceTypeEnum.GATEWAY.value, "id": str(gateway_id)}],
    }


def build_gateway_member_snapshot(members: Iterable[GatewayMember]) -> dict[str, GatewayMemberAuthorization]:
    return {
        member.username: GatewayMemberAuthorization(role=member.role, expires=member.expires) for member in members
    }


def _revoke(
    gateway_id: int,
    authorizations: Iterable[tuple[str, str]],
    operated_by: str,
) -> None:
    payloads = [
        build_gateway_revoke_authorization(username, role, gateway_id) for username, role in sorted(authorizations)
    ]
    for payload_chunk in chunked(payloads):
        revoke_authorization(payload_chunk, operated_by)


def _grant(
    gateway_id: int,
    snapshot: GatewayMemberSnapshot,
    usernames: Iterable[str],
    operated_by: str,
) -> None:
    now = timezone.now()
    payloads = [
        build_gateway_authorization(
            username,
            snapshot[username].role,
            gateway_id,
            snapshot[username].expires,
            now=now,
        )
        for username in sorted(usernames)
    ]
    for payload_chunk in chunked(payloads):
        add_authorization(payload_chunk, operated_by)


def _restore_gateway_member_snapshot(
    gateway_id: int,
    before: GatewayMemberSnapshot,
    after: GatewayMemberSnapshot,
    operated_by: str,
) -> None:
    changed_usernames = {
        username for username in before.keys() | after.keys() if before.get(username) != after.get(username)
    }
    authorizations_to_clear = {
        (username, snapshot[username].role)
        for snapshot in (before, after)
        for username in changed_usernames
        if username in snapshot
    }
    _revoke(gateway_id, authorizations_to_clear, operated_by)
    _grant(gateway_id, before, changed_usernames & before.keys(), operated_by)


def apply_gateway_member_snapshots_to_iam(
    gateway_id: int,
    before: GatewayMemberSnapshot,
    after: GatewayMemberSnapshot,
    operated_by: str,
) -> None:
    """Apply a local member delta and compensate IAM back to ``before`` on failure."""
    usernames = before.keys() | after.keys()
    authorizations_to_revoke = {
        (username, before[username].role)
        for username in usernames
        if username in before and (username not in after or before[username].role != after[username].role)
    }
    usernames_to_grant = {
        username
        for username in usernames
        if username in after and (username not in before or before[username] != after[username])
    }

    if not authorizations_to_revoke and not usernames_to_grant:
        return

    try:
        _revoke(gateway_id, authorizations_to_revoke, operated_by)
        _grant(gateway_id, after, usernames_to_grant, operated_by)
    except Exception:
        try:
            _restore_gateway_member_snapshot(gateway_id, before, after, operated_by)
        except Exception:
            logger.critical(
                "failed to compensate gateway IAM authorizations, gateway_id=%s",
                gateway_id,
                exc_info=True,
            )
        raise
