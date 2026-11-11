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
"""Business-facing gateway member operations."""

import logging
from dataclasses import dataclass
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.utils.translation import gettext as _
from pydantic import BaseModel, ConfigDict, Field

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.iam import (
    GatewayMemberSnapshot,
    apply_gateway_member_snapshots_to_iam,
    build_gateway_member_snapshot,
)
from apigateway.common.error_codes import error_codes
from apigateway.common.tenant.request import is_configured_excluded_username
from apigateway.components.bkpaas import update_app_maintainers
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)


class GatewayMemberInput(BaseModel):
    """Typed member payload for gateway member writes."""

    model_config = ConfigDict(frozen=True)

    username: str = Field(min_length=1, max_length=64)
    role: GatewayRoleEnum


@dataclass(frozen=True)
class GatewayMemberBatchCreateResult:
    created: list[GatewayMember]
    skipped: list[GatewayMember]


@dataclass(frozen=True)
class GatewayMemberRoleUpdateResult:
    member: GatewayMember
    previous_role: str
    changed: bool


@dataclass(frozen=True)
class ExcludedMemberCleanupResult:
    delete_usernames: list[str]
    skipped_last_administrators: list[str]


def _lock_gateway(gateway: Gateway) -> Gateway:
    return Gateway.objects.select_for_update().get(pk=gateway.pk)


def _get_gateway_member_snapshot(gateway_id: int) -> GatewayMemberSnapshot:
    return build_gateway_member_snapshot(GatewayMember.objects.filter(gateway_id=gateway_id))


def _administrator_usernames(snapshot: GatewayMemberSnapshot) -> list[str]:
    return sorted(
        username
        for username, authorization in snapshot.items()
        if authorization.role == GatewayRoleEnum.ADMINISTRATOR.value
    )


def _without_excluded_usernames(gateway_id: int, usernames: Iterable[str]) -> list[str]:
    kept: list[str] = []
    excluded: list[str] = []
    for username in usernames:
        if is_configured_excluded_username(username):
            if username not in excluded:
                excluded.append(username)
            continue
        kept.append(username)
    if excluded:
        logger.warning(
            "skip excluded gateway members, gateway_id=%s usernames=%s",
            gateway_id,
            excluded,
        )
    return kept


def _without_excluded_members(
    gateway_id: int,
    members: Iterable[GatewayMemberInput],
) -> list[GatewayMemberInput]:
    kept: list[GatewayMemberInput] = []
    excluded: list[str] = []
    for member in members:
        if is_configured_excluded_username(member.username):
            if member.username not in excluded:
                excluded.append(member.username)
            continue
        kept.append(member)
    if excluded:
        logger.warning(
            "skip excluded gateway members, gateway_id=%s usernames=%s",
            gateway_id,
            excluded,
        )
    return kept


def _excluded_member_cleanup_plan(members: Iterable[GatewayMember]) -> ExcludedMemberCleanupResult:
    member_list = list(members)
    excluded_administrators = sorted(
        member.username
        for member in member_list
        if member.role == GatewayRoleEnum.ADMINISTRATOR.value and is_configured_excluded_username(member.username)
    )
    excluded_administrator_set = set(excluded_administrators)
    excluded_others = sorted(
        member.username
        for member in member_list
        if member.username not in excluded_administrator_set and is_configured_excluded_username(member.username)
    )
    has_remaining_administrator = any(
        member.role == GatewayRoleEnum.ADMINISTRATOR.value and member.username not in excluded_administrator_set
        for member in member_list
    )
    if has_remaining_administrator:
        return ExcludedMemberCleanupResult(
            delete_usernames=sorted([*excluded_others, *excluded_administrators]),
            skipped_last_administrators=[],
        )
    return ExcludedMemberCleanupResult(
        delete_usernames=excluded_others,
        skipped_last_administrators=excluded_administrators,
    )


def _sync_external_member_state(
    gateway: Gateway,
    before: GatewayMemberSnapshot,
    operated_by: str,
    *,
    sync_paas: bool,
) -> None:
    after = _get_gateway_member_snapshot(gateway.id)
    if before == after:
        return

    before_administrators = _administrator_usernames(before)
    after_administrators = _administrator_usernames(after)
    paas_synced = False

    if sync_paas and gateway.is_programmable and before_administrators != after_administrators:
        _sync_programmable_gateway_administrators(gateway)
        paas_synced = True

    try:
        if settings.BK_IAM_V4_ENABLED:
            apply_gateway_member_snapshots_to_iam(gateway, before, after, operated_by)
    except Exception:
        if paas_synced:
            try:
                update_app_maintainers(gateway.name, before_administrators)
            except Exception:
                logger.critical(
                    "failed to compensate programmable gateway maintainers, gateway_id=%s",
                    gateway.id,
                    exc_info=True,
                )
        raise


@transaction.atomic
def replace_gateway_administrators(
    gateway: Gateway,
    usernames: Iterable[str],
    operated_by: str,
) -> list[str]:
    """Replace all gateway administrators."""
    target_usernames = _without_excluded_usernames(gateway.id, usernames)
    if not target_usernames:
        raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)

    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    result = GatewayMember.objects.replace_gateway_administrators(
        locked_gateway.id,
        set(target_usernames),
        operated_by,
    )
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=False)
    return result


@transaction.atomic
def add_gateway_administrators(
    gateway: Gateway,
    usernames: Iterable[str],
    operated_by: str,
) -> list[str]:
    """Add gateway administrators without removing existing ones."""
    target_usernames = _without_excluded_usernames(gateway.id, usernames)
    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    result = GatewayMember.objects.add_gateway_administrators(
        locked_gateway.id,
        set(target_usernames),
        operated_by,
    )
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=False)
    return result


def _unique_members(members: Iterable[GatewayMemberInput]) -> list[GatewayMemberInput]:
    items = list(members)
    usernames = [item.username for item in items]
    if len(usernames) != len(set(usernames)):
        raise error_codes.INVALID_ARGUMENT.format(_("同一用户不能重复提交。"), replace=True)
    return items


@transaction.atomic
def add_gateway_members(
    gateway: Gateway,
    members: Iterable[GatewayMemberInput],
    operated_by: str,
) -> GatewayMemberBatchCreateResult:
    """Add gateway members, skipping usernames that already exist."""
    unique_members = _unique_members(_without_excluded_members(gateway.id, members))
    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    created, skipped = GatewayMember.objects.add_gateway_members(
        locked_gateway.id,
        unique_members,
        operated_by,
    )
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=True)
    return GatewayMemberBatchCreateResult(created=created, skipped=skipped)


@transaction.atomic
def update_gateway_member_role(
    gateway: Gateway,
    member_id: int,
    role: GatewayRoleEnum,
    operated_by: str,
) -> GatewayMemberRoleUpdateResult:
    """Update one member role while preserving at least one administrator."""
    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    member, previous_role, changed = GatewayMember.objects.update_gateway_member_role(
        locked_gateway.id,
        member_id,
        role,
        operated_by,
    )
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=True)
    return GatewayMemberRoleUpdateResult(member=member, previous_role=previous_role, changed=changed)


@transaction.atomic
def delete_gateway_member(gateway: Gateway, member_id: int, operated_by: str) -> GatewayMember:
    """Delete one member while preserving at least one administrator."""
    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    result = GatewayMember.objects.delete_gateway_member(locked_gateway.id, member_id)
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=True)
    return result


@transaction.atomic
def delete_gateway_members(gateway: Gateway, usernames: Iterable[str], operated_by: str) -> list[GatewayMember]:
    """Delete members by username without syncing the result back to PaaS."""
    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    result = GatewayMember.objects.delete_gateway_members_by_usernames(locked_gateway.id, usernames)
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=False)
    return result


def remove_excluded_gateway_members(
    gateway: Gateway,
    operated_by: str,
    *,
    apply: bool = True,
) -> ExcludedMemberCleanupResult:
    """Delete excluded members while keeping at least one administrator."""
    plan = _excluded_member_cleanup_plan(GatewayMember.objects.list_gateway_members(gateway.id))
    if not apply or not plan.delete_usernames:
        return plan
    deleted_members = delete_gateway_members(gateway, plan.delete_usernames, operated_by)
    return ExcludedMemberCleanupResult(
        delete_usernames=[member.username for member in deleted_members],
        skipped_last_administrators=plan.skipped_last_administrators,
    )


def _sync_programmable_gateway_administrators(gateway: Gateway) -> None:
    update_app_maintainers(
        gateway.name,
        GatewayMember.objects.list_gateway_administrators(gateway.id),
    )


def build_gateway_doc_maintainers(gateway: Gateway, administrators: list[str]) -> dict:
    """Build document maintainers, falling back to gateway administrators."""
    if not gateway.doc_maintainers or gateway.doc_maintainers.get("type") == "":
        return {
            "type": "user",
            "contacts": administrators,
            "service_account": {
                "name": "",
                "link": "",
            },
        }
    return gateway.doc_maintainers
