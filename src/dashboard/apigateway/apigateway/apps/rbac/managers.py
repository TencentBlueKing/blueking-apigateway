from __future__ import annotations

from collections import defaultdict
from datetime import timedelta
from typing import TYPE_CHECKING, Iterable

from django.db import models, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.exceptions import (
    GatewayMemberInvalidArgumentError,
    GatewayMemberNotFoundError,
    LastGatewayAdministratorError,
)

if TYPE_CHECKING:
    from apigateway.apps.rbac.models import GatewayMember

GATEWAY_MEMBER_EXPIRE_DAYS = 365


class GatewayMemberManager(models.Manager):
    def list_gateway_members(self, gateway_id: int) -> list[GatewayMember]:
        return list(self.filter(gateway_id=gateway_id).order_by("role", "username"))

    def list_gateway_administrators(self, gateway_id: int) -> list[str]:
        return list(
            self.filter(
                gateway_id=gateway_id,
                role=GatewayRoleEnum.ADMINISTRATOR.value,
            )
            .order_by("username")
            .values_list("username", flat=True)
        )

    def list_gateway_approvers(self, gateway_id: int) -> list[str]:
        operators = list(
            self.filter(
                gateway_id=gateway_id,
                role=GatewayRoleEnum.OPERATOR.value,
            )
            .order_by("username")
            .values_list("username", flat=True)
        )
        if operators:
            return operators
        return self.list_gateway_administrators(gateway_id)

    def build_gateway_administrators_map(self, gateway_ids: Iterable[int]) -> dict[int, list[str]]:
        result: dict[int, list[str]] = defaultdict(list)
        members = (
            self.filter(
                gateway_id__in=set(gateway_ids),
                role=GatewayRoleEnum.ADMINISTRATOR.value,
            )
            .order_by("gateway_id", "username")
            .values_list("gateway_id", "username")
        )
        for gateway_id, username in members:
            result[gateway_id].append(username)
        return dict(result)

    def build_gateway_approvers_map(self, gateway_ids: Iterable[int]) -> dict[int, list[str]]:
        administrators: dict[int, list[str]] = defaultdict(list)
        operators: dict[int, list[str]] = defaultdict(list)
        members = (
            self.filter(
                gateway_id__in=set(gateway_ids),
                role__in=(GatewayRoleEnum.ADMINISTRATOR.value, GatewayRoleEnum.OPERATOR.value),
            )
            .order_by("gateway_id", "username")
            .values_list("gateway_id", "username", "role")
        )
        for gateway_id, username, role in members:
            if role == GatewayRoleEnum.OPERATOR.value:
                operators[gateway_id].append(username)
            else:
                administrators[gateway_id].append(username)

        return {
            gateway_id: operators.get(gateway_id) or administrators[gateway_id]
            for gateway_id in administrators.keys() | operators.keys()
        }

    def is_gateway_administrator(self, gateway_id: int, username: str) -> bool:
        return self.filter(
            gateway_id=gateway_id,
            username=username,
            role=GatewayRoleEnum.ADMINISTRATOR.value,
        ).exists()

    def has_gateway_approve_permission(self, gateway_id: int, username: str) -> bool:
        return self.filter(
            gateway_id=gateway_id,
            username=username,
            role__in=(GatewayRoleEnum.ADMINISTRATOR.value, GatewayRoleEnum.OPERATOR.value),
        ).exists()

    def list_gateway_ids_by_username(self, username: str, roles: Iterable[str]) -> list[int]:
        return list(
            self.filter(
                username=username,
                role__in=roles,
            ).values_list("gateway_id", flat=True)
        )

    def list_gateway_ids_by_approver(self, username: str) -> list[int]:
        operator_members = self.model._default_manager.filter(
            gateway_id=OuterRef("gateway_id"),
            role=GatewayRoleEnum.OPERATOR.value,
        )
        return list(
            self.get_queryset()
            .annotate(_gateway_has_operator=Exists(operator_members))
            .filter(
                Q(
                    username=username,
                    role=GatewayRoleEnum.OPERATOR.value,
                )
                | Q(
                    username=username,
                    role=GatewayRoleEnum.ADMINISTRATOR.value,
                    _gateway_has_operator=False,
                )
            )
            .values_list("gateway_id", flat=True)
        )

    def replace_gateway_administrators(
        self,
        gateway_id: int,
        usernames: Iterable[str],
        operated_by: str,
    ) -> list[str]:
        return self._update_gateway_administrators(gateway_id, usernames, operated_by, replace=True)

    def add_gateway_administrators(
        self,
        gateway_id: int,
        usernames: Iterable[str],
        operated_by: str,
    ) -> list[str]:
        return self._update_gateway_administrators(gateway_id, usernames, operated_by, replace=False)

    @transaction.atomic
    def add_gateway_members(
        self,
        gateway_id: int,
        members: Iterable[tuple[str, str]],
        operated_by: str,
    ) -> tuple[list[GatewayMember], list[GatewayMember]]:
        requested_members = list(members)
        usernames = [username for username, _ in requested_members]
        if len(usernames) != len(set(usernames)):
            raise GatewayMemberInvalidArgumentError("Duplicate usernames are not allowed.")

        valid_roles = set(GatewayRoleEnum.get_values())
        if any(role not in valid_roles for _, role in requested_members):
            raise GatewayMemberInvalidArgumentError("Invalid gateway member role.")

        existing_members = self._lock_gateway_members(gateway_id)
        now = timezone.now()
        expires = now + timedelta(days=GATEWAY_MEMBER_EXPIRE_DAYS)
        members_to_create = [
            self.model(
                gateway_id=gateway_id,
                username=username,
                role=role,
                expires=expires,
                created_by=operated_by,
                updated_by=operated_by,
            )
            for username, role in requested_members
            if username not in existing_members
        ]
        if members_to_create:
            self.bulk_create(members_to_create)

        created_usernames = {member.username for member in members_to_create}
        created_members_by_username = {
            member.username: member for member in self.filter(gateway_id=gateway_id, username__in=created_usernames)
        }
        created_members = [
            created_members_by_username[username] for username, _ in requested_members if username in created_usernames
        ]
        skipped_members = [
            existing_members[username] for username, _ in requested_members if username in existing_members
        ]
        return created_members, skipped_members

    @transaction.atomic
    def update_gateway_member_role(
        self,
        gateway_id: int,
        member_id: int,
        role: str,
        operated_by: str,
    ) -> tuple[GatewayMember, str, bool]:
        if role not in GatewayRoleEnum.get_values():
            raise GatewayMemberInvalidArgumentError("Invalid gateway member role.")

        members = self._lock_gateway_members(gateway_id)
        member = next((member for member in members.values() if member.id == member_id), None)
        if member is None:
            raise GatewayMemberNotFoundError

        previous_role = member.role
        if previous_role == role:
            return member, previous_role, False

        if previous_role == GatewayRoleEnum.ADMINISTRATOR.value:
            administrator_count = sum(item.role == GatewayRoleEnum.ADMINISTRATOR.value for item in members.values())
            if administrator_count <= 1:
                raise LastGatewayAdministratorError

        now = timezone.now()
        member.role = role
        member.updated_by = operated_by
        member.updated_time = now
        member.save(update_fields=["role", "updated_by", "updated_time"])
        return member, previous_role, True

    @transaction.atomic
    def delete_gateway_member(self, gateway_id: int, member_id: int) -> GatewayMember:
        members = self._lock_gateway_members(gateway_id)
        member = next((member for member in members.values() if member.id == member_id), None)
        if member is None:
            raise GatewayMemberNotFoundError

        if member.role == GatewayRoleEnum.ADMINISTRATOR.value:
            administrator_count = sum(item.role == GatewayRoleEnum.ADMINISTRATOR.value for item in members.values())
            if administrator_count <= 1:
                raise LastGatewayAdministratorError

        self.filter(id=member.id).delete()
        return member

    def _lock_gateway_members(self, gateway_id: int) -> dict[str, GatewayMember]:
        # Lock all member rows of the target gateway for write operations.
        return {member.username: member for member in self.select_for_update().filter(gateway_id=gateway_id)}

    @transaction.atomic
    def _update_gateway_administrators(
        self,
        gateway_id: int,
        usernames: Iterable[str],
        operated_by: str,
        *,
        replace: bool,
    ) -> list[str]:
        target_usernames = set(usernames)
        if replace and not target_usernames:
            raise LastGatewayAdministratorError

        members = self._lock_gateway_members(gateway_id)
        if replace:
            administrator_ids_to_delete = [
                member.id
                for member in members.values()
                if member.role == GatewayRoleEnum.ADMINISTRATOR.value and member.username not in target_usernames
            ]
            if administrator_ids_to_delete:
                self.filter(id__in=administrator_ids_to_delete).delete()

        now = timezone.now()
        expires = now + timedelta(days=GATEWAY_MEMBER_EXPIRE_DAYS)
        members_to_create = []
        members_to_update = []
        for username in target_usernames:
            member = members.get(username)
            if member is None:
                members_to_create.append(
                    self.model(
                        gateway_id=gateway_id,
                        username=username,
                        role=GatewayRoleEnum.ADMINISTRATOR.value,
                        expires=expires,
                        created_by=operated_by,
                        updated_by=operated_by,
                    )
                )
                continue

            if member.role != GatewayRoleEnum.ADMINISTRATOR.value:
                member.role = GatewayRoleEnum.ADMINISTRATOR.value
                member.expires = expires
                member.updated_by = operated_by
                member.updated_time = now
                members_to_update.append(member)

        if members_to_create:
            self.bulk_create(members_to_create)
        if members_to_update:
            self.bulk_update(members_to_update, ["role", "expires", "updated_by", "updated_time"])

        return self.list_gateway_administrators(gateway_id)
