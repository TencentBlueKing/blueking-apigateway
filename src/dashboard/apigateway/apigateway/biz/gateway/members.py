"""Business-facing gateway member operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Iterable

from django.db import transaction
from django.utils.translation import gettext as _

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.exceptions import (
    GatewayMemberInvalidArgumentError,
    GatewayMemberNotFoundError,
    LastGatewayAdministratorError,
)
from apigateway.apps.rbac.models import GatewayMember
from apigateway.common.error_codes import error_codes
from apigateway.components.bkpaas import update_app_maintainers

if TYPE_CHECKING:
    from apigateway.core.models import Gateway


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


@transaction.atomic
def add_gateway_members(
    gateway: Gateway,
    members: Iterable[tuple[str, str]],
    operated_by: str,
) -> GatewayMemberBatchCreateResult:
    """Add gateway members, skipping usernames that already exist."""
    try:
        created, skipped = GatewayMember.objects.add_gateway_members(gateway.id, members, operated_by)
    except GatewayMemberInvalidArgumentError:
        raise error_codes.INVALID_ARGUMENT.format(_("网关成员参数不合法。"), replace=True)

    if gateway.is_programmable and any(member.role == GatewayRoleEnum.ADMINISTRATOR.value for member in created):
        _sync_programmable_gateway_administrators(gateway)

    return GatewayMemberBatchCreateResult(created=created, skipped=skipped)


@transaction.atomic
def update_gateway_member_role(
    gateway: Gateway,
    member_id: int,
    role: str,
    operated_by: str,
) -> GatewayMemberRoleUpdateResult:
    """Update one member role while preserving at least one administrator."""
    try:
        member, previous_role, changed = GatewayMember.objects.update_gateway_member_role(
            gateway.id,
            member_id,
            role,
            operated_by,
        )
    except LastGatewayAdministratorError:
        raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)
    except GatewayMemberNotFoundError:
        raise error_codes.NOT_FOUND.format(_("网关成员不存在。"), replace=True)
    except GatewayMemberInvalidArgumentError:
        raise error_codes.INVALID_ARGUMENT.format(_("网关成员角色不合法。"), replace=True)

    if gateway.is_programmable and changed and previous_role != role:
        _sync_programmable_gateway_administrators(gateway)

    return GatewayMemberRoleUpdateResult(member=member, previous_role=previous_role, changed=changed)


@transaction.atomic
def delete_gateway_member(gateway: Gateway, member_id: int) -> GatewayMember:
    """Delete one member while preserving at least one administrator."""
    try:
        member = GatewayMember.objects.delete_gateway_member(gateway.id, member_id)
    except LastGatewayAdministratorError:
        raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)
    except GatewayMemberNotFoundError:
        raise error_codes.NOT_FOUND.format(_("网关成员不存在。"), replace=True)

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
