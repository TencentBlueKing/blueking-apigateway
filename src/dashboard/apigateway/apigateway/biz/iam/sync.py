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
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta

from django.db import transaction
from django.utils import timezone

from apigateway.apps.rbac.constants import GatewayResourceTypeEnum, GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.components.bkiam import (
    DEFAULT_PAGE_SIZE,
    AuthorizationSubjectQueryPayload,
    add_authorization,
    chunked,
    list_authorization_subject,
    revoke_authorization,
)
from apigateway.core.models import Gateway

from .authorization import build_gateway_authorization, build_gateway_revoke_authorization
from .constants import (
    DEFAULT_MEMBER_EXPIRY,
    EXPIRY_REFRESH_GRANT,
    EXPIRY_TOLERANCE,
    EXTRA_REVOKE,
    MISSING_GRANT,
    ROLE_MISMATCH_GRANT,
    ROLE_MISMATCH_REVOKE,
)


@dataclass(frozen=True, order=True)
class GatewayIAMAuthorization:
    """One user-role authorization for a gateway."""

    username: str
    role: str
    expired_at: int


@dataclass(frozen=True, order=True)
class GatewayIAMSyncItem:
    """One deterministic grant or revoke operation."""

    username: str
    role: str
    expired_at: int
    reason: str


@dataclass(frozen=True)
class GatewayIAMSyncResult:
    gateway_id: int
    gateway_name: str
    grants: tuple[GatewayIAMSyncItem, ...]
    revokes: tuple[GatewayIAMSyncItem, ...]
    unchanged: int
    applied: bool = False

    @property
    def grant_count(self) -> int:
        return len(self.grants)

    @property
    def revoke_count(self) -> int:
        return len(self.revokes)

    @property
    def change_count(self) -> int:
        return self.grant_count + self.revoke_count


class GatewayIAMAuthorizationSynchronizer:
    """Plan and apply local-authoritative GatewayMember reconciliation."""

    def __init__(
        self,
        *,
        page_size: int = DEFAULT_PAGE_SIZE,
        expiry_tolerance: timedelta = EXPIRY_TOLERANCE,
    ):
        if page_size <= 0:
            raise ValueError("page_size must be greater than zero")
        if expiry_tolerance < timedelta(0):
            raise ValueError("expiry_tolerance must not be negative")
        self._page_size = page_size
        self._expiry_tolerance_seconds = int(expiry_tolerance.total_seconds())

    def reconcile_gateway(
        self,
        gateway_id: int,
        *,
        apply: bool,
        operator: str,
        username: str | None = None,
    ) -> GatewayIAMSyncResult:
        if not apply:
            gateway = Gateway.objects.get(pk=gateway_id)
            return self._plan_gateway(gateway, username=username)

        with transaction.atomic():
            # This must be the first database read in the transaction. Online
            # member writes take the same lock before reading GatewayMember.
            gateway = Gateway.objects.select_for_update().get(pk=gateway_id)
            result = self._plan_gateway(gateway, username=username)
            self._apply(result, operator)
            return replace(result, applied=True)

    def _plan_gateway(self, gateway: Gateway, *, username: str | None) -> GatewayIAMSyncResult:
        now = timezone.now()
        desired = self._get_desired_authorizations(gateway.id, now=now)
        actual = self._get_iam_authorizations(gateway.id)
        if username is not None:
            desired = {key: item for key, item in desired.items() if item.username == username}
            actual = {key: item for key, item in actual.items() if item.username == username}
        return self._build_result(gateway, desired, actual)

    def _get_desired_authorizations(
        self,
        gateway_id: int,
        *,
        now: datetime,
    ) -> dict[tuple[str, str], GatewayIAMAuthorization]:
        desired: dict[tuple[str, str], GatewayIAMAuthorization] = {}
        known_roles = set(GatewayRoleEnum.get_values())
        members = GatewayMember.objects.filter(gateway_id=gateway_id).order_by("username", "role")
        for member in members:
            if member.role not in known_roles:
                raise ValueError(f"gateway {gateway_id} member {member.username!r} has unknown role {member.role!r}")
            expires = member.expires or now + DEFAULT_MEMBER_EXPIRY
            item = GatewayIAMAuthorization(
                username=member.username,
                role=member.role,
                expired_at=int(expires.timestamp()),
            )
            desired[(item.username, item.role)] = item
        return desired

    def _get_iam_authorizations(self, gateway_id: int) -> dict[tuple[str, str], GatewayIAMAuthorization]:
        authorizations: dict[tuple[str, str], GatewayIAMAuthorization] = {}
        for role in sorted(GatewayRoleEnum.get_values()):
            for item in self._list_role_authorizations(gateway_id, role):
                key = (item.username, item.role)
                previous = authorizations.get(key)
                if previous is not None and previous != item:
                    raise ValueError(
                        f"IAM returned duplicate authorizations with different expiry for "
                        f"gateway {gateway_id}, user {item.username!r}, role {role!r}"
                    )
                authorizations[key] = item
        return authorizations

    def _list_role_authorizations(self, gateway_id: int, role: str) -> list[GatewayIAMAuthorization]:
        page = 1
        authorizations: list[GatewayIAMAuthorization] = []
        while True:
            payload: AuthorizationSubjectQueryPayload = {
                "role_id": role,
                "related_resource_type_id": GatewayResourceTypeEnum.GATEWAY.value,
                "resource": {
                    "type": GatewayResourceTypeEnum.GATEWAY.value,
                    "id": str(gateway_id),
                },
                "page": page,
                "page_size": self._page_size,
            }
            data = list_authorization_subject(payload)
            authorizations.extend(
                GatewayIAMAuthorization(
                    username=result["id"],
                    role=role,
                    expired_at=result["expired_at"],
                )
                for result in data["results"]
            )

            if len(authorizations) >= data["count"]:
                break
            if not data["results"]:
                raise ValueError(f"IAM pagination ended before count for gateway {gateway_id}, role {role!r}")
            page += 1
        return authorizations

    def _build_result(
        self,
        gateway: Gateway,
        desired: dict[tuple[str, str], GatewayIAMAuthorization],
        actual: dict[tuple[str, str], GatewayIAMAuthorization],
    ) -> GatewayIAMSyncResult:
        grants: list[GatewayIAMSyncItem] = []
        revokes: list[GatewayIAMSyncItem] = []
        unchanged = 0

        actual_roles_by_username: dict[str, set[str]] = {}
        for authorization in actual.values():
            actual_roles_by_username.setdefault(authorization.username, set()).add(authorization.role)

        for key, authorization in sorted(desired.items()):
            current = actual.get(key)
            if current is None:
                reason = ROLE_MISMATCH_GRANT if actual_roles_by_username.get(authorization.username) else MISSING_GRANT
                grants.append(
                    GatewayIAMSyncItem(
                        username=authorization.username,
                        role=authorization.role,
                        expired_at=authorization.expired_at,
                        reason=reason,
                    )
                )
            elif abs(current.expired_at - authorization.expired_at) > self._expiry_tolerance_seconds:
                grants.append(
                    GatewayIAMSyncItem(
                        username=authorization.username,
                        role=authorization.role,
                        expired_at=authorization.expired_at,
                        reason=EXPIRY_REFRESH_GRANT,
                    )
                )
            else:
                unchanged += 1

        desired_by_username = {authorization.username: authorization for authorization in desired.values()}
        for key, authorization in sorted(actual.items()):
            expected = desired_by_username.get(authorization.username)
            if key in desired:
                continue
            reason = ROLE_MISMATCH_REVOKE if expected is not None else EXTRA_REVOKE
            revokes.append(
                GatewayIAMSyncItem(
                    username=authorization.username,
                    role=authorization.role,
                    expired_at=authorization.expired_at,
                    reason=reason,
                )
            )

        return GatewayIAMSyncResult(
            gateway_id=gateway.id,
            gateway_name=gateway.name,
            grants=tuple(sorted(grants)),
            revokes=tuple(sorted(revokes)),
            unchanged=unchanged,
        )

    def _apply(self, result: GatewayIAMSyncResult, operator: str) -> None:
        revoke_payloads = [
            build_gateway_revoke_authorization(item.username, item.role, result.gateway_id) for item in result.revokes
        ]
        grant_payloads = [
            build_gateway_authorization(
                item.username,
                item.role,
                result.gateway_id,
                datetime.fromtimestamp(item.expired_at, tz=UTC),
            )
            for item in result.grants
        ]

        for revoke_batch in chunked(revoke_payloads):
            revoke_authorization(revoke_batch, operator)
        for grant_batch in chunked(grant_payloads):
            add_authorization(grant_batch, operator)
