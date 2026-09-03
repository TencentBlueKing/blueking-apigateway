from collections import defaultdict
from datetime import timedelta
from typing import Iterable

from django.db import models, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone

from apigateway.apps.rbac.constants import GatewayRoleEnum

GATEWAY_MEMBER_EXPIRE_DAYS = 365


class GatewayMemberManager(models.Manager):
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
            raise ValueError("A gateway must have at least one administrator.")

        members = {member.username: member for member in self.select_for_update().filter(gateway_id=gateway_id)}
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
                member.updated_by = operated_by
                member.updated_time = now
                members_to_update.append(member)

        if members_to_create:
            self.bulk_create(members_to_create)
        if members_to_update:
            self.bulk_update(members_to_update, ["role", "updated_by", "updated_time"])

        return self.list_gateway_administrators(gateway_id)
