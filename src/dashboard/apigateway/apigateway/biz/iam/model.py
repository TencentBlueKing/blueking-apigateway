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

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, TypedDict, cast

from django.conf import settings
from django.utils.encoding import force_str

from apigateway.apps.rbac.constants import (
    BK_IAM_V4_SYSTEM_ID,
    GATEWAY_ROLE_ACTIONS,
    GatewayActionEnum,
    GatewayResourceTypeEnum,
    GatewayRoleEnum,
)
from apigateway.components import bkiam

from .constants import SYSTEM_DESCRIPTION, SYSTEM_NAME

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


class GatewayIAMModel(TypedDict):
    resource_types: list[bkiam.ResourceTypePayload]
    actions: list[bkiam.ActionPayload]
    roles: list[bkiam.RolePayload]


def get_gateway_iam_model() -> GatewayIAMModel:
    """Build the IAM model from the local RBAC declarations."""
    resource_type_id = GatewayResourceTypeEnum.GATEWAY.value
    action_names = dict(GatewayActionEnum.get_choices())
    role_names = dict(GatewayRoleEnum.get_choices())

    return {
        "resource_types": [
            {
                "id": resource_type_id,
                "name": force_str(GatewayResourceTypeEnum.get_choice_label(resource_type_id)),
                "ancestors": [],
            }
        ],
        "actions": [
            {
                "id": action_id,
                "name": force_str(action_names[action_id]),
                "resource_type_id": resource_type_id,
            }
            for action_id in GatewayActionEnum.get_values()
        ],
        "roles": [
            {
                "id": role_id,
                "name": force_str(role_names[role_id]),
                "description": f"蓝鲸 API 网关{force_str(role_names[role_id])}角色",
                "actions": [
                    {
                        "id": action_id,
                        "resource_type_id": resource_type_id,
                    }
                    for action_id in GATEWAY_ROLE_ACTIONS[role_id]
                ],
            }
            for role_id in GatewayRoleEnum.get_values()
        ],
    }


@dataclass(frozen=True)
class GatewayIAMModelSyncResult:
    created: int = 0
    updated: int = 0
    unchanged: int = 0
    action_bindings_added: int = 0
    action_bindings_deleted: int = 0
    action_bindings_unchanged: int = 0


class GatewayIAMModelSyncer:
    def sync(self) -> GatewayIAMModelSyncResult:
        desired_model = get_gateway_iam_model()
        counts = {
            "created": 0,
            "updated": 0,
            "unchanged": 0,
            "action_bindings_added": 0,
            "action_bindings_deleted": 0,
            "action_bindings_unchanged": 0,
        }

        self._sync_system(counts)
        self._sync_resource_types(desired_model["resource_types"], counts)
        self._sync_actions(desired_model["actions"], counts)
        self._sync_roles(desired_model["roles"], counts)

        return GatewayIAMModelSyncResult(**counts)

    def _sync_system(self, counts: dict[str, int]) -> None:
        desired: bkiam.SystemPayload = {
            "id": BK_IAM_V4_SYSTEM_ID,
            "name": SYSTEM_NAME,
            "description": SYSTEM_DESCRIPTION,
            "managers": list(settings.BK_IAM_V4_MANAGERS),
            "clients": [settings.BK_APP_CODE],
            "callback_url": "",
        }
        try:
            existing = bkiam.retrieve_system()
        except bkiam.BkIamNotFoundError:
            bkiam.create_system(desired)
            counts["created"] += 1
            return

        changes = _changed_fields(existing, desired, ("name", "description", "managers", "clients", "callback_url"))
        if changes:
            bkiam.update_system(cast("bkiam.SystemUpdatePayload", changes))
            counts["updated"] += 1
        else:
            counts["unchanged"] += 1

    def _sync_resource_types(self, desired_items: list[bkiam.ResourceTypePayload], counts: dict[str, int]) -> None:
        existing_by_id = _by_id(_list_all(bkiam.list_resource_type))
        missing: list[bkiam.ResourceTypePayload] = []

        for desired in desired_items:
            existing = existing_by_id.get(desired["id"])
            if existing is None:
                missing.append(desired)
                continue

            changes = _changed_fields(existing, desired, ("name", "ancestors"))
            if changes:
                bkiam.update_resource_type(
                    desired["id"],
                    cast("bkiam.ResourceTypeUpdatePayload", changes),
                )
                counts["updated"] += 1
            else:
                counts["unchanged"] += 1

        for batch in bkiam.chunked(missing):
            bkiam.batch_create_resource_type(batch)
            counts["created"] += len(batch)

    def _sync_actions(self, desired_items: list[bkiam.ActionPayload], counts: dict[str, int]) -> None:
        existing_by_id = _by_id(_list_all(bkiam.list_action))
        missing: list[bkiam.ActionPayload] = []

        for desired in desired_items:
            existing = existing_by_id.get(desired["id"])
            if existing is None:
                missing.append(desired)
                continue

            if existing.get("resource_type_id", "") != desired.get("resource_type_id", ""):
                raise ValueError(
                    f"IAM action {desired['id']!r} has immutable resource_type_id "
                    f"{existing.get('resource_type_id', '')!r}, expected {desired.get('resource_type_id', '')!r}"
                )
            changes = _changed_fields(existing, desired, ("name",))
            if changes:
                bkiam.update_action(desired["id"], cast("bkiam.ActionUpdatePayload", changes))
                counts["updated"] += 1
            else:
                counts["unchanged"] += 1

        for batch in bkiam.chunked(missing):
            bkiam.batch_create_action(batch)
            counts["created"] += len(batch)

    def _sync_roles(self, desired_items: list[bkiam.RolePayload], counts: dict[str, int]) -> None:
        existing_by_id = _by_id(_list_all(bkiam.list_role))
        missing: list[bkiam.RolePayload] = []
        existing_roles: list[tuple[bkiam.RolePayload, dict[str, Any]]] = []

        for desired in desired_items:
            existing = existing_by_id.get(desired["id"])
            if existing is None:
                missing.append(desired)
                counts["action_bindings_added"] += len(desired["actions"])
                continue

            changes = _changed_fields(existing, desired, ("name", "description"))
            if changes:
                bkiam.update_role(desired["id"], cast("bkiam.RoleUpdatePayload", changes))
                counts["updated"] += 1
            else:
                counts["unchanged"] += 1
            existing_roles.append((desired, existing))

        for batch in bkiam.chunked(missing):
            bkiam.batch_create_role(batch)
            counts["created"] += len(batch)

        for desired, existing in existing_roles:
            self._sync_role_actions(desired, existing, counts)

    def _sync_role_actions(
        self,
        desired: bkiam.RolePayload,
        existing: dict[str, Any],
        counts: dict[str, int],
    ) -> None:
        desired_by_id = _by_id(desired.get("actions", []))
        existing_by_id = _by_id(existing.get("actions", []))
        desired_ids = set(desired_by_id)
        existing_ids = set(existing_by_id)

        changed_ids = {
            action_id
            for action_id in desired_ids & existing_ids
            if desired_by_id[action_id].get("resource_type_id", "")
            != existing_by_id[action_id].get("resource_type_id", "")
        }
        additions = [desired_by_id[action_id] for action_id in sorted((desired_ids - existing_ids) | changed_ids)]
        deletions = sorted((existing_ids - desired_ids) | changed_ids)
        counts["action_bindings_added"] += len(additions)
        counts["action_bindings_deleted"] += len(deletions)
        counts["action_bindings_unchanged"] += len((desired_ids & existing_ids) - changed_ids)

        for deletion_batch in bkiam.chunked(deletions):
            bkiam.batch_delete_role_action(desired["id"], deletion_batch)
        for addition_batch in bkiam.chunked(additions):
            bkiam.batch_create_role_action(
                desired["id"],
                cast("list[bkiam.RoleActionPayload]", addition_batch),
            )


def _changed_fields(
    existing: dict[str, Any],
    desired: Mapping[str, Any],
    mutable_fields: Sequence[str],
) -> dict[str, Any]:
    return {
        field: desired[field] for field in mutable_fields if field in desired and existing.get(field) != desired[field]
    }


def _list_all(list_page: Callable[..., bkiam.PaginationData]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    page = 1
    while True:
        page_data = list_page(page=page, page_size=bkiam.DEFAULT_PAGE_SIZE)
        results = page_data["results"]
        items.extend(results)
        if len(items) >= page_data["count"] or not results:
            return items
        page += 1


def _by_id(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {item["id"]: item for item in items}
