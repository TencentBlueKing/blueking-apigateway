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

from collections import defaultdict
from datetime import timedelta
from typing import TYPE_CHECKING, Iterable, Protocol

from django.db import models, transaction
from django.db.models import Exists, OuterRef, Q
from django.utils import timezone
from django.utils.translation import gettext as _

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.common.error_codes import error_codes

if TYPE_CHECKING:
    from apigateway.apps.rbac.models import GatewayMember

GATEWAY_MEMBER_EXPIRE_DAYS = 365


class _GatewayMemberInput(Protocol):
    username: str
    role: GatewayRoleEnum


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
        members: Iterable[_GatewayMemberInput],
        operated_by: str,
    ) -> tuple[list[GatewayMember], list[GatewayMember]]:
        requested_members = list(members)
        existing_members = self._lock_gateway_members(gateway_id)
        now = timezone.now()
        expires = now + timedelta(days=GATEWAY_MEMBER_EXPIRE_DAYS)
        members_to_create = [
            self.model(
                gateway_id=gateway_id,
                username=member.username,
                role=member.role.value,
                expires=expires,
                created_by=operated_by,
                updated_by=operated_by,
            )
            for member in requested_members
            if member.username not in existing_members
        ]
        if members_to_create:
            self.bulk_create(members_to_create)

        created_usernames = {member.username for member in members_to_create}
        created_members_by_username = {
            member.username: member for member in self.filter(gateway_id=gateway_id, username__in=created_usernames)
        }
        created_members = [
            created_members_by_username[member.username]
            for member in requested_members
            if member.username in created_usernames
        ]
        skipped_members = [
            existing_members[member.username] for member in requested_members if member.username in existing_members
        ]
        return created_members, skipped_members

    @transaction.atomic
    def update_gateway_member_role(
        self,
        gateway_id: int,
        member_id: int,
        role: GatewayRoleEnum,
        operated_by: str,
    ) -> tuple[GatewayMember, str, bool]:
        member = self._lock_gateway_member(gateway_id, member_id)
        previous_role = member.role
        if previous_role == role.value:
            return member, previous_role, False

        if self._is_last_administrator(gateway_id, member):
            raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)

        now = timezone.now()
        member.role = role.value
        member.updated_by = operated_by
        member.updated_time = now
        member.save(update_fields=["role", "updated_by", "updated_time"])
        return member, previous_role, True

    @transaction.atomic
    def delete_gateway_member(self, gateway_id: int, member_id: int) -> GatewayMember:
        member = self._lock_gateway_member(gateway_id, member_id)
        if self._is_last_administrator(gateway_id, member):
            raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)

        self.filter(id=member.id).delete()
        return member

    def _lock_gateway_member(self, gateway_id: int, member_id: int) -> GatewayMember:
        try:
            return self.select_for_update().get(gateway_id=gateway_id, id=member_id)
        except self.model.DoesNotExist:
            raise error_codes.NOT_FOUND.format(_("网关成员不存在。"), replace=True)

    def _is_last_administrator(self, gateway_id: int, member: GatewayMember) -> bool:
        if member.role != GatewayRoleEnum.ADMINISTRATOR.value:
            return False
        return (
            not self.filter(
                gateway_id=gateway_id,
                role=GatewayRoleEnum.ADMINISTRATOR.value,
            )
            .exclude(id=member.id)
            .exists()
        )

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
            raise error_codes.FAILED_PRECONDITION.format(_("网关至少需要保留一个管理员。"), replace=True)

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
