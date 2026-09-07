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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from django.db import transaction
from django.utils.translation import gettext as _
from pydantic import BaseModel, ConfigDict, Field

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.common.error_codes import error_codes
from apigateway.components.bkpaas import update_app_maintainers

if TYPE_CHECKING:
    from apigateway.core.models import Gateway


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


def replace_gateway_administrators(
    gateway: Gateway,
    usernames: Iterable[str],
    operated_by: str,
) -> list[str]:
    """Replace all gateway administrators."""
    target_usernames = set(usernames)
    if not target_usernames:
        raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)

    return GatewayMember.objects.replace_gateway_administrators(
        gateway.id,
        target_usernames,
        operated_by,
    )


def add_gateway_administrators(
    gateway: Gateway,
    usernames: Iterable[str],
    operated_by: str,
) -> list[str]:
    """Add gateway administrators without removing existing ones."""
    return GatewayMember.objects.add_gateway_administrators(
        gateway.id,
        usernames,
        operated_by,
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
    created, skipped = GatewayMember.objects.add_gateway_members(
        gateway.id,
        _unique_members(members),
        operated_by,
    )

    if gateway.is_programmable and any(member.role == GatewayRoleEnum.ADMINISTRATOR.value for member in created):
        _sync_programmable_gateway_administrators(gateway)

    return GatewayMemberBatchCreateResult(created=created, skipped=skipped)


@transaction.atomic
def update_gateway_member_role(
    gateway: Gateway,
    member_id: int,
    role: GatewayRoleEnum,
    operated_by: str,
) -> GatewayMemberRoleUpdateResult:
    """Update one member role while preserving at least one administrator."""
    member, previous_role, changed = GatewayMember.objects.update_gateway_member_role(
        gateway.id,
        member_id,
        role,
        operated_by,
    )

    if gateway.is_programmable and changed:
        _sync_programmable_gateway_administrators(gateway)

    return GatewayMemberRoleUpdateResult(member=member, previous_role=previous_role, changed=changed)


@transaction.atomic
def delete_gateway_member(gateway: Gateway, member_id: int) -> GatewayMember:
    """Delete one member while preserving at least one administrator."""
    member = GatewayMember.objects.delete_gateway_member(gateway.id, member_id)

    if gateway.is_programmable and member.role == GatewayRoleEnum.ADMINISTRATOR.value:
        _sync_programmable_gateway_administrators(gateway)

    return member


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
