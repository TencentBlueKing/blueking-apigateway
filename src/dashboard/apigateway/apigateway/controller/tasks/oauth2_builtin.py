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

"""同步 OAuth2 public/personal 内置应用的资源权限。

本模块由发布流程同步调用，并非独立的 Celery 任务：

1. 配置下发前调用 ``prepare_publish``，根据待发布版本和其它环境的已发布版本补齐权限。
   此阶段只新增或规范化权限，不删除，避免旧配置仍在数据面生效时权限被提前回收。
2. 发布、滚动更新或下架成功，以及环境或数据面绑定关系删除后，调用 ``reconcile_gateway``，
   根据所有生效环境的版本重新收敛权限。只有相关发布或下架操作在全部活跃数据面完成后，
   才会删除不再需要的权限；该入口也可通过管理命令执行检查或修复。

期望权限以资源版本快照为准，不读取编辑区资源；同一网关的计算和写入由 Redis 锁串行化。
"""

from dataclasses import dataclass
from typing import TypeAlias

import redis_lock
from django.conf import settings
from django.db import transaction

from apigateway.apps.data_plane.constants import get_resource_auth_config
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.apps.permission.constants import (
    OAUTH2_BUILTIN_APP_CODES,
    OAUTH2_PERSONAL_CLIENT_APP_CODE,
    OAUTH2_PUBLIC_CLIENT_APP_CODE,
    GrantTypeEnum,
)
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.core.constants import (
    PublishEventStatusEnum,
    ReleaseHistoryStatusEnum,
)
from apigateway.core.models import Gateway, PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.utils.exception import LockTimeout
from apigateway.utils.redis_utils import get_default_redis_client
from apigateway.utils.time import NeverExpiresTime

BuiltinPermission: TypeAlias = tuple[str, int]


@dataclass(frozen=True)
class ReconciliationBlocker:
    """记录阻止旧权限删除的环境和数据面发布状态。"""

    stage_id: int
    stage_name: str
    data_plane_id: int
    data_plane_name: str
    release_history_id: int | None
    status: str


@dataclass(frozen=True)
class OAuth2BuiltinPermissionResult:
    """权限收敛结果，也用于 ``apply=False`` 时预览差异。"""

    desired: frozenset[BuiltinPermission]
    missing: frozenset[BuiltinPermission]
    extra: frozenset[BuiltinPermission]
    unchanged: frozenset[BuiltinPermission]
    normalized: frozenset[BuiltinPermission]
    deletion_blocked: bool
    blockers: tuple[ReconciliationBlocker, ...]
    applied: bool


def _required_permissions(resource_version: ResourceVersion, stage: Stage) -> set[BuiltinPermission]:
    """从指定环境的资源版本快照中提取需要授予内置应用的权限。"""

    required: set[BuiltinPermission] = set()
    for resource in resource_version.data:
        if stage.name in resource.get("disabled_stages", []):
            continue

        auth_config = get_resource_auth_config(resource)
        if not auth_config.get("app_verified_required", True):
            continue
        if not auth_config.get("resource_perm_required", True):
            continue

        resource_id = resource["id"]
        if auth_config.get("oauth2_public_client_enabled", False):
            required.add((OAUTH2_PUBLIC_CLIENT_APP_CODE, resource_id))
        if auth_config.get("oauth2_personal_client_enabled", False):
            required.add((OAUTH2_PERSONAL_CLIENT_APP_CODE, resource_id))
    return required


class OAuth2BuiltinPermissionReconciler:
    """将网关的 OAuth2 内置应用权限收敛到已发布配置所需的状态。

    收敛包含新增缺失权限、规范化已有权限，以及在数据面状态安全时删除多余权限。
    所有操作只影响 ``public`` 和 ``personal`` 两个内置应用，不处理普通 SaaS 或 MCP 虚拟应用。
    """

    def prepare_publish(
        self,
        gateway: Gateway,
        stage: Stage,
        candidate_version: ResourceVersion,
    ) -> OAuth2BuiltinPermissionResult:
        """在配置下发前准备权限，使用待发布版本替换目标环境版本且不删除旧权限。"""

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
        """在发布状态变化后按所有生效环境重新收敛权限。

        发布、滚动更新或下架成功，以及环境或数据面绑定关系删除后都会触发此方法；管理命令
        也通过此入口检查或修复权限。``apply=False`` 仅计算并返回差异，不写入数据库。
        """

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
        lock = redis_lock.Lock(
            get_default_redis_client(),
            f"oauth2_builtin_permission:{gateway.id}",
            expire=settings.REDIS_PUBLISH_LOCK_TIMEOUT,
            auto_renewal=True,
            strict=False,
        )
        if not lock.acquire(
            blocking=True,
            timeout=settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES,
        ):
            raise LockTimeout("Timeout while waiting for OAuth2 built-in permission lock")
        try:
            return self._reconcile_locked(
                gateway,
                candidate=candidate,
                allow_delete=allow_delete,
                apply=apply,
            )
        finally:
            lock.release()

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

        permission_map = {
            (permission.bk_app_code, permission.resource_id): permission
            for permission in AppResourcePermission.objects.filter(
                gateway=gateway,
                bk_app_code__in=OAUTH2_BUILTIN_APP_CODES,
            )
        }
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
        """合并各生效环境的权限；发布前以候选版本替换目标环境的当前版本。"""

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
        """找出尚未收敛到当前发布状态的环境和活跃数据面组合。

        新权限可以提前添加，但只要存在任一阻塞项，就保留全部旧权限。这样可避免多数据面灰度
        发布期间，仍运行旧配置的数据面因权限被提前删除而拒绝请求。
        """

        data_planes = GatewayDataPlaneBinding.objects.get_gateway_active_data_planes(gateway.id)
        if not releases or not data_planes:
            return ()

        stage_ids = [release.stage_id for release in releases]
        data_plane_ids = [data_plane.id for data_plane in data_planes]
        latest_history_map: dict[tuple[int, int], ReleaseHistory] = {}
        histories = ReleaseHistory.objects.filter(
            gateway=gateway,
            stage_id__in=stage_ids,
            data_plane_id__in=data_plane_ids,
        ).order_by("stage_id", "data_plane_id", "-id")
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
                status: str | None
                if history is None:
                    status = "missing_history"
                else:
                    latest_event = latest_event_map.get(history.id)
                    if latest_event is None:
                        status = "missing_event"
                    else:
                        status = self._get_blocker_status(latest_event)
                        if (
                            status is None
                            and release.stage.is_active
                            and history.resource_version_id != release.resource_version_id
                        ):
                            status = "version_mismatch"

                if status is not None:
                    blockers.append(
                        self._make_blocker(
                            release,
                            data_plane,
                            release_history_id=history.id if history is not None else None,
                            status=status,
                        )
                    )

        return tuple(blockers)

    @staticmethod
    def _get_blocker_status(latest_event: PublishEvent) -> str | None:
        """将最新发布事件转换为阻塞原因；成功时返回 ``None``。"""

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
            return None
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
    ) -> None:
        """在一个事务中新增、规范化并按需删除内置应用权限。"""

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
