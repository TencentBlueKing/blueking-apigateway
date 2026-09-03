"""Business-facing gateway member operations."""

from __future__ import annotations

from typing import TYPE_CHECKING, Iterable

from django.utils.translation import gettext as _

from apigateway.apps.rbac.models import GatewayMember
from apigateway.common.error_codes import error_codes

if TYPE_CHECKING:
    from apigateway.core.models import Gateway


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
