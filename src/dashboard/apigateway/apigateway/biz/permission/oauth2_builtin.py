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

import json
from dataclasses import dataclass
from typing import TypeAlias

from django.conf import settings
from django.db import transaction

from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.apps.permission.constants import OAUTH2_BUILTIN_APP_CODES, GrantTypeEnum
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.core.constants import (
    PublishEventStatusEnum,
    ReleaseHistoryStatusEnum,
)
from apigateway.core.models import Gateway, PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.utils.redis_utils import Lock
from apigateway.utils.time import NeverExpiresTime

BuiltinPermission: TypeAlias = tuple[str, int]


@dataclass(frozen=True)
class ReconciliationBlocker:
    stage_id: int
    stage_name: str
    data_plane_id: int
    data_plane_name: str
    release_history_id: int | None
    status: str


@dataclass(frozen=True)
class OAuth2BuiltinPermissionResult:
    desired: frozenset[BuiltinPermission]
    missing: frozenset[BuiltinPermission]
    extra: frozenset[BuiltinPermission]
    unchanged: frozenset[BuiltinPermission]
    normalized: frozenset[BuiltinPermission]
    deletion_blocked: bool
    blockers: tuple[ReconciliationBlocker, ...]
    applied: bool


def _required_permissions(resource_version: ResourceVersion, stage: Stage) -> set[BuiltinPermission]:
    required: set[BuiltinPermission] = set()
    for resource in resource_version.data:
        if stage.name in resource.get("disabled_stages", []):
            continue

        auth_config = json.loads(resource["contexts"]["resource_auth"]["config"])
        if not auth_config.get("app_verified_required", True):
            continue
        if not auth_config.get("resource_perm_required", True):
            continue

        resource_id = resource["id"]
        if auth_config.get("oauth2_public_client_enabled", False):
            required.add(("public", resource_id))
        if auth_config.get("oauth2_personal_client_enabled", False):
            required.add(("personal", resource_id))
    return required


class OAuth2BuiltinPermissionReconciler:
    def prepare_publish(
        self,
        gateway: Gateway,
        stage: Stage,
        candidate_version: ResourceVersion,
    ) -> OAuth2BuiltinPermissionResult:
        return self._run(
            gateway,
            candidate=(stage, candidate_version),
            allow_delete=False,
            apply=True,
        )

    def reconcile_gateway(
        self,
        gateway: Gateway,
        *,
        apply: bool = True,
    ) -> OAuth2BuiltinPermissionResult:
        return self._run(
            gateway,
            candidate=None,
            allow_delete=True,
            apply=apply,
        )

    def _run(
        self,
        gateway: Gateway,
        *,
        candidate: tuple[Stage, ResourceVersion] | None,
        allow_delete: bool,
        apply: bool,
    ) -> OAuth2BuiltinPermissionResult:
        with Lock(
            f"oauth2_builtin_permission:{gateway.id}",
            timeout=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
            try_get_times=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
        ):
            return self._reconcile_locked(
                gateway,
                candidate=candidate,
                allow_delete=allow_delete,
                apply=apply,
            )

    def _reconcile_locked(
        self,
        gateway: Gateway,
        *,
        candidate: tuple[Stage, ResourceVersion] | None,
        allow_delete: bool,
        apply: bool,
    ) -> OAuth2BuiltinPermissionResult:
        releases = list(Release.objects.filter(gateway=gateway).select_related("stage", "resource_version"))
        desired = self._get_desired_permissions(gateway, releases, candidate)
        blockers = self._get_convergence_blockers(gateway, releases)

        permissions = list(
            AppResourcePermission.objects.filter(
                gateway=gateway,
                bk_app_code__in=OAUTH2_BUILTIN_APP_CODES,
            )
        )
        permission_map = {(permission.bk_app_code, permission.resource_id): permission for permission in permissions}
        existing = frozenset(permission_map)
        desired_frozen = frozenset(desired)
        missing = desired_frozen - existing
        extra = existing - desired_frozen
        unchanged = desired_frozen & existing
        normalized = frozenset(
            permission for permission in unchanged if self._needs_normalization(permission_map[permission])
        )

        if apply:
            self._apply(
                gateway,
                desired=desired_frozen,
                missing=missing,
                extra=extra,
                allow_delete=allow_delete and not blockers,
            )

        return OAuth2BuiltinPermissionResult(
            desired=desired_frozen,
            missing=missing,
            extra=extra,
            unchanged=unchanged,
            normalized=normalized,
            deletion_blocked=bool(blockers),
            blockers=blockers,
            applied=apply,
        )

    @staticmethod
    def _get_desired_permissions(
        gateway: Gateway,
        releases: list[Release],
        candidate: tuple[Stage, ResourceVersion] | None,
    ) -> set[BuiltinPermission]:
        desired: set[BuiltinPermission] = set()
        candidate_stage_id = candidate[0].id if candidate else None

        if gateway.is_active:
            for release in releases:
                if release.stage_id == candidate_stage_id:
                    continue
                if release.stage.is_active:
                    desired.update(_required_permissions(release.resource_version, release.stage))

        if candidate:
            desired.update(_required_permissions(candidate[1], candidate[0]))

        return desired

    def _get_convergence_blockers(
        self,
        gateway: Gateway,
        releases: list[Release],
    ) -> tuple[ReconciliationBlocker, ...]:
        data_planes = GatewayDataPlaneBinding.objects.get_gateway_active_data_planes(gateway.id)
        if not releases or not data_planes:
            return ()

        stage_ids = [release.stage_id for release in releases]
        data_plane_ids = [data_plane.id for data_plane in data_planes]
        latest_history_map: dict[tuple[int, int], ReleaseHistory] = {}
        histories = (
            ReleaseHistory.objects.filter(
                gateway=gateway,
                stage_id__in=stage_ids,
                data_plane_id__in=data_plane_ids,
            )
            .select_related("resource_version")
            .order_by("stage_id", "data_plane_id", "-id")
        )
        for history in histories:
            latest_history_map.setdefault(
                (history.stage_id, history.data_plane_id),
                history,
            )

        latest_event_map = PublishEvent.objects.get_release_history_id_to_latest_publish_event_map(
            [history.id for history in latest_history_map.values()]
        )
        blockers: list[ReconciliationBlocker] = []
        for release in releases:
            for data_plane in data_planes:
                history = latest_history_map.get((release.stage_id, data_plane.id))
                if history is None:
                    blockers.append(
                        self._make_blocker(
                            release,
                            data_plane,
                            release_history_id=None,
                            status="missing_history",
                        )
                    )
                    continue

                latest_event = latest_event_map.get(history.id)
                if latest_event is None:
                    blockers.append(
                        self._make_blocker(
                            release,
                            data_plane,
                            release_history_id=history.id,
                            status="missing_event",
                        )
                    )
                    continue

                status = self._get_blocker_status(latest_event)
                if status:
                    blockers.append(
                        self._make_blocker(
                            release,
                            data_plane,
                            release_history_id=history.id,
                            status=status,
                        )
                    )
                    continue

                if release.stage.is_active and history.resource_version_id != release.resource_version_id:
                    blockers.append(
                        self._make_blocker(
                            release,
                            data_plane,
                            release_history_id=history.id,
                            status="version_mismatch",
                        )
                    )

        return tuple(blockers)

    @staticmethod
    def _get_blocker_status(latest_event: PublishEvent) -> str:
        known_event_statuses = {
            PublishEventStatusEnum.SUCCESS.value,
            PublishEventStatusEnum.FAILURE.value,
            PublishEventStatusEnum.PENDING.value,
            PublishEventStatusEnum.DOING.value,
        }
        if latest_event.status not in known_event_statuses:
            return "unknown"

        status = latest_event.get_release_history_status()
        if status == ReleaseHistoryStatusEnum.SUCCESS.value:
            return ""
        if status == ReleaseHistoryStatusEnum.FAILURE.value:
            if latest_event.status == PublishEventStatusEnum.FAILURE.value:
                return "failure"
            return "timeout"
        if status == ReleaseHistoryStatusEnum.DOING.value:
            return "doing"
        return "unknown"

    @staticmethod
    def _make_blocker(
        release: Release,
        data_plane: DataPlane,
        *,
        release_history_id: int | None,
        status: str,
    ) -> ReconciliationBlocker:
        return ReconciliationBlocker(
            stage_id=release.stage_id,
            stage_name=release.stage.name,
            data_plane_id=data_plane.id,
            data_plane_name=data_plane.name,
            release_history_id=release_history_id,
            status=status,
        )

    @staticmethod
    def _needs_normalization(permission: AppResourcePermission) -> bool:
        return (
            permission.expires != NeverExpiresTime.time
            or permission.grant_type != GrantTypeEnum.OAUTH2_BUILTIN.value
            or permission.handled_by != "system"
        )

    @staticmethod
    def _apply(
        gateway: Gateway,
        *,
        desired: frozenset[BuiltinPermission],
        missing: frozenset[BuiltinPermission],
        extra: frozenset[BuiltinPermission],
        allow_delete: bool,
    ):
        defaults = {
            "expires": NeverExpiresTime.time,
            "grant_type": GrantTypeEnum.OAUTH2_BUILTIN.value,
            "handled_by": "system",
        }
        with transaction.atomic():
            AppResourcePermission.objects.bulk_create(
                [
                    AppResourcePermission(
                        gateway=gateway,
                        bk_app_code=app_code,
                        resource_id=resource_id,
                        **defaults,
                    )
                    for app_code, resource_id in missing
                ],
                ignore_conflicts=True,
            )

            for app_code in OAUTH2_BUILTIN_APP_CODES:
                resource_ids = [
                    resource_id for desired_app_code, resource_id in desired if desired_app_code == app_code
                ]
                if resource_ids:
                    AppResourcePermission.objects.filter(
                        gateway=gateway,
                        bk_app_code=app_code,
                        resource_id__in=resource_ids,
                    ).update(**defaults)

            if allow_delete:
                for app_code in OAUTH2_BUILTIN_APP_CODES:
                    resource_ids = [resource_id for extra_app_code, resource_id in extra if extra_app_code == app_code]
                    if resource_ids:
                        AppResourcePermission.objects.filter(
                            gateway=gateway,
                            bk_app_code=app_code,
                            resource_id__in=resource_ids,
                        ).delete()
