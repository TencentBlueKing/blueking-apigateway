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

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, Iterable, TypeVar

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
from apigateway.components.bkpaas import update_app_maintainers
from apigateway.core.models import Gateway

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


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
            apply_gateway_member_snapshots_to_iam(gateway.id, before, after, operated_by)
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


def _write_gateway_members(
    gateway: Gateway,
    operated_by: str,
    mutate: Callable[[Gateway], _T],
    *,
    sync_paas: bool,
) -> _T:
    locked_gateway = _lock_gateway(gateway)
    before = _get_gateway_member_snapshot(locked_gateway.id)
    result = mutate(locked_gateway)
    _sync_external_member_state(locked_gateway, before, operated_by, sync_paas=sync_paas)
    return result


@transaction.atomic
def replace_gateway_administrators(
    gateway: Gateway,
    usernames: Iterable[str],
    operated_by: str,
) -> list[str]:
    """Replace all gateway administrators."""
    target_usernames = set(usernames)
    if not target_usernames:
        raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)

    return _write_gateway_members(
        gateway,
        operated_by,
        lambda locked: GatewayMember.objects.replace_gateway_administrators(
            locked.id,
            target_usernames,
            operated_by,
        ),
        sync_paas=False,
    )


@transaction.atomic
def add_gateway_administrators(
    gateway: Gateway,
    usernames: Iterable[str],
    operated_by: str,
) -> list[str]:
    """Add gateway administrators without removing existing ones."""
    return _write_gateway_members(
        gateway,
        operated_by,
        lambda locked: GatewayMember.objects.add_gateway_administrators(
            locked.id,
            set(usernames),
            operated_by,
        ),
        sync_paas=False,
    )


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
    created, skipped = _write_gateway_members(
        gateway,
        operated_by,
        lambda locked: GatewayMember.objects.add_gateway_members(
            locked.id,
            _unique_members(members),
            operated_by,
        ),
        sync_paas=True,
    )
    return GatewayMemberBatchCreateResult(created=created, skipped=skipped)


@transaction.atomic
def update_gateway_member_role(
    gateway: Gateway,
    member_id: int,
    role: GatewayRoleEnum,
    operated_by: str,
) -> GatewayMemberRoleUpdateResult:
    """Update one member role while preserving at least one administrator."""
    member, previous_role, changed = _write_gateway_members(
        gateway,
        operated_by,
        lambda locked: GatewayMember.objects.update_gateway_member_role(
            locked.id,
            member_id,
            role,
            operated_by,
        ),
        sync_paas=True,
    )
    return GatewayMemberRoleUpdateResult(member=member, previous_role=previous_role, changed=changed)


@transaction.atomic
def delete_gateway_member(gateway: Gateway, member_id: int, operated_by: str) -> GatewayMember:
    """Delete one member while preserving at least one administrator."""
    return _write_gateway_members(
        gateway,
        operated_by,
        lambda locked: GatewayMember.objects.delete_gateway_member(locked.id, member_id),
        sync_paas=True,
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
