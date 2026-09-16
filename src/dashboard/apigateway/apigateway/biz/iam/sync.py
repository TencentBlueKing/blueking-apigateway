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
    iter_authorization_subjects,
    revoke_authorization,
)
from apigateway.core.models import Gateway

from .authorization import build_gateway_authorization, build_gateway_revoke_authorization
from .constants import (
    DEFAULT_MEMBER_EXPIRY,
    EXPIRY_TOLERANCE,
    REASON_EXPIRY_REFRESH_GRANT,
    REASON_EXTRA_REVOKE,
    REASON_MISSING_GRANT,
    REASON_ROLE_MISMATCH_GRANT,
    REASON_ROLE_MISMATCH_REVOKE,
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
            return self._build_reconciliation_plan(gateway, username=username)

        with transaction.atomic():
            # This must be the first database read in the transaction. Online
            # member writes take the same lock before reading GatewayMember.
            gateway = Gateway.objects.select_for_update().get(pk=gateway_id)
            plan = self._build_reconciliation_plan(gateway, username=username)
            self._apply_plan(plan, operator)
            return replace(plan, applied=True)

    def _build_reconciliation_plan(self, gateway: Gateway, *, username: str | None) -> GatewayIAMSyncResult:
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
        members = GatewayMember.objects.filter(gateway_id=gateway_id).order_by("username", "role")
        for member in members:
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
                authorizations[(item.username, item.role)] = item
        return authorizations

    def _list_role_authorizations(self, gateway_id: int, role: str) -> list[GatewayIAMAuthorization]:
        payload: AuthorizationSubjectQueryPayload = {
            "role_id": role,
            "related_resource_type_id": GatewayResourceTypeEnum.GATEWAY.value,
            "resource": {
                "type": GatewayResourceTypeEnum.GATEWAY.value,
                "id": str(gateway_id),
            },
            "page_size": self._page_size,
        }
        return [
            GatewayIAMAuthorization(
                username=item["id"],
                role=role,
                expired_at=item["expired_at"],
            )
            for item in iter_authorization_subjects(payload)
        ]

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
                reason = (
                    REASON_ROLE_MISMATCH_GRANT
                    if actual_roles_by_username.get(authorization.username)
                    else REASON_MISSING_GRANT
                )
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
                        reason=REASON_EXPIRY_REFRESH_GRANT,
                    )
                )
            else:
                unchanged += 1

        desired_by_username = {authorization.username: authorization for authorization in desired.values()}
        for key, authorization in sorted(actual.items()):
            expected = desired_by_username.get(authorization.username)
            if key in desired:
                continue
            reason = REASON_ROLE_MISMATCH_REVOKE if expected is not None else REASON_EXTRA_REVOKE
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

    def _apply_plan(self, plan: GatewayIAMSyncResult, operator: str) -> None:
        revoke_payloads = [
            build_gateway_revoke_authorization(item.username, item.role, plan.gateway_id) for item in plan.revokes
        ]
        grant_payloads = [
            build_gateway_authorization(
                item.username,
                item.role,
                plan.gateway_id,
                datetime.fromtimestamp(item.expired_at, tz=UTC),
            )
            for item in plan.grants
        ]

        for revoke_batch in chunked(revoke_payloads):
            revoke_authorization(revoke_batch, operator)
        for grant_batch in chunked(grant_payloads):
            add_authorization(grant_batch, operator)
