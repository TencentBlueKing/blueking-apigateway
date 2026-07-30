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
from datetime import timedelta

import pytest
from ddf import G
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apigateway.apps.data_plane.constants import DataPlaneStatusEnum
from apigateway.apps.data_plane.models import DataPlane, GatewayDataPlaneBinding
from apigateway.apps.permission.models import AppResourcePermission
from apigateway.controller.tasks.oauth2_builtin import OAuth2BuiltinPermissionReconciler
from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishEventNameTypeEnum,
    PublishEventStatusEnum,
    StageStatusEnum,
)
from apigateway.core.models import PublishEvent, Release, ReleaseHistory, ResourceVersion, Stage
from apigateway.utils.time import NeverExpiresTime

pytestmark = pytest.mark.django_db


def make_resource_snapshot(
    resource_id: int,
    *,
    stage_name: str,
    support_public: bool,
    support_personal: bool,
    app_verified_required: bool = True,
    resource_perm_required: bool = True,
    disabled: bool = False,
) -> dict:
    return {
        "id": resource_id,
        "name": f"resource-{resource_id}",
        "disabled_stages": [stage_name] if disabled else [],
        "contexts": {
            "resource_auth": {
                "config": json.dumps(
                    {
                        "auth_verified_required": True,
                        "app_verified_required": app_verified_required,
                        "resource_perm_required": resource_perm_required,
                        "oauth2_public_client_enabled": support_public,
                        "oauth2_personal_client_enabled": support_personal,
                    }
                )
            }
        },
    }


def make_resource_version(gateway, version: str, resources: list[dict]) -> ResourceVersion:
    return G(ResourceVersion, gateway=gateway, version=version, _data=json.dumps(resources))


def make_stage_release(gateway, stage_name: str, version: str, resources: list[dict], *, active: bool = True):
    stage = G(
        Stage,
        gateway=gateway,
        name=stage_name,
        status=StageStatusEnum.ACTIVE.value if active else StageStatusEnum.INACTIVE.value,
    )
    resource_version = make_resource_version(gateway, version, resources)
    release = G(Release, gateway=gateway, stage=stage, resource_version=resource_version)
    return stage, resource_version, release


def bind_data_plane(gateway, name: str) -> DataPlane:
    data_plane = G(DataPlane, name=name, status=DataPlaneStatusEnum.ACTIVE.value)
    G(GatewayDataPlaneBinding, gateway=gateway, data_plane=data_plane)
    return data_plane


def make_history_event(release, data_plane, status: str, *, resource_version=None, name=None):
    history = G(
        ReleaseHistory,
        gateway=release.gateway,
        stage=release.stage,
        resource_version=resource_version or release.resource_version,
        data_plane=data_plane,
    )
    event = G(
        PublishEvent,
        gateway=release.gateway,
        stage=release.stage,
        publish=history,
        name=name or PublishEventNameTypeEnum.LOAD_CONFIGURATION.value,
        step=PublishEventNameTypeEnum.get_event_step(name or PublishEventNameTypeEnum.LOAD_CONFIGURATION.value),
        status=status,
    )
    return history, event


@pytest.fixture(autouse=True)
def mock_permission_lock(mocker):
    return mocker.patch("apigateway.controller.tasks.oauth2_builtin.redis_lock.Lock")


def test_reconcile_uses_auto_renewing_owned_lock(fake_gateway, mock_permission_lock, mocker, settings):
    settings.REDIS_PUBLISH_LOCK_TIMEOUT = 5
    settings.REDIS_PUBLISH_LOCK_RETRY_GET_TIMES = 3
    redis_client = mocker.patch(
        "apigateway.controller.tasks.oauth2_builtin.get_default_redis_client",
        return_value=mocker.sentinel.redis_client,
    )
    lock = mock_permission_lock.return_value
    lock.acquire.return_value = True

    OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway, apply=False)

    redis_client.assert_called_once_with()
    mock_permission_lock.assert_called_once_with(
        mocker.sentinel.redis_client,
        f"oauth2_builtin_permission:{fake_gateway.id}",
        expire=5,
        auto_renewal=True,
        strict=False,
    )
    lock.acquire.assert_called_once_with(blocking=True, timeout=5)
    lock.release.assert_called_once_with()


def test_reconcile_calculates_permissions_from_real_snapshot_flags(fake_gateway):
    stage_name = "prod"
    resources = [
        make_resource_snapshot(1, stage_name=stage_name, support_public=True, support_personal=False),
        make_resource_snapshot(2, stage_name=stage_name, support_public=False, support_personal=True),
        make_resource_snapshot(3, stage_name=stage_name, support_public=True, support_personal=True),
        make_resource_snapshot(4, stage_name=stage_name, support_public=False, support_personal=False),
        make_resource_snapshot(
            5,
            stage_name=stage_name,
            support_public=True,
            support_personal=True,
            app_verified_required=False,
        ),
        make_resource_snapshot(
            6,
            stage_name=stage_name,
            support_public=True,
            support_personal=True,
            resource_perm_required=False,
        ),
        make_resource_snapshot(
            7,
            stage_name=stage_name,
            support_public=True,
            support_personal=True,
            disabled=True,
        ),
    ]
    make_stage_release(fake_gateway, stage_name, "1.0.0", resources)

    result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway, apply=False)

    assert result.desired == frozenset(
        {
            ("public", 1),
            ("personal", 2),
            ("public", 3),
            ("personal", 3),
        }
    )
    assert result.missing == result.desired
    assert result.applied is False
    assert not AppResourcePermission.objects.filter(gateway=fake_gateway).exists()


def test_reconcile_ignores_snapshot_without_resource_auth_context(fake_gateway):
    make_stage_release(fake_gateway, "prod", "1.0.0", [{"id": 1}])

    result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway, apply=False)

    assert result.desired == frozenset()


def test_reconcile_uses_union_of_active_release_snapshots_not_editing_resources(fake_gateway):
    make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(101, stage_name="prod", support_public=True, support_personal=False)],
    )
    make_stage_release(
        fake_gateway,
        "test",
        "2.0.0",
        [make_resource_snapshot(202, stage_name="test", support_public=False, support_personal=True)],
    )
    make_stage_release(
        fake_gateway,
        "inactive",
        "3.0.0",
        [make_resource_snapshot(303, stage_name="inactive", support_public=True, support_personal=True)],
        active=False,
    )

    result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway, apply=False)

    assert result.desired == frozenset({("public", 101), ("personal", 202)})


def test_prepare_publish_replaces_target_stage_and_never_deletes(fake_gateway):
    target_stage, _, _ = make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(1, stage_name="prod", support_public=True, support_personal=False)],
        active=False,
    )
    make_stage_release(
        fake_gateway,
        "test",
        "1.0.0",
        [make_resource_snapshot(2, stage_name="test", support_public=False, support_personal=True)],
    )
    candidate = make_resource_version(
        fake_gateway,
        "2.0.0",
        [make_resource_snapshot(3, stage_name="prod", support_public=True, support_personal=True)],
    )
    G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=1,
        bk_app_code="public",
        grant_type="oauth2_builtin",
        expires=NeverExpiresTime.time,
    )
    G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=99,
        bk_app_code="personal",
        grant_type="oauth2_builtin",
        expires=NeverExpiresTime.time,
    )

    result = OAuth2BuiltinPermissionReconciler().prepare_publish(fake_gateway, target_stage, candidate)

    assert result.desired == frozenset({("personal", 2), ("public", 3), ("personal", 3)})
    assert result.to_delete == frozenset({("public", 1), ("personal", 99)})
    assert {
        (permission.bk_app_code, permission.resource_id)
        for permission in AppResourcePermission.objects.filter(gateway=fake_gateway)
    } == {
        ("public", 1),
        ("personal", 2),
        ("public", 3),
        ("personal", 3),
        ("personal", 99),
    }


def test_reconcile_creates_desired_rows_without_follow_up_updates_and_preserves_unrelated_permissions(fake_gateway):
    make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(1, stage_name="prod", support_public=True, support_personal=False)],
    )
    saas = G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=1,
        bk_app_code="normal-saas",
        grant_type="initialize",
        handled_by="admin",
    )
    virtual = G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=1,
        bk_app_code="v_mcp_1",
        grant_type="initialize",
        handled_by="admin",
    )

    with CaptureQueriesContext(connection) as queries:
        result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway)

    builtin = AppResourcePermission.objects.get(gateway=fake_gateway, resource_id=1, bk_app_code="public")
    assert builtin.expires == NeverExpiresTime.time
    assert builtin.grant_type == "oauth2_builtin"
    assert builtin.handled_by == "system"
    saas.refresh_from_db()
    virtual.refresh_from_db()
    assert (saas.grant_type, saas.handled_by) == ("initialize", "admin")
    assert (virtual.grant_type, virtual.handled_by) == ("initialize", "admin")

    permission_updates = [
        query["sql"]
        for query in queries
        if query["sql"].lstrip().upper().startswith("UPDATE") and "permission_app_resource" in query["sql"]
    ]
    assert result.missing == frozenset({("public", 1)})
    assert result.to_delete == frozenset()
    assert result.unchanged == frozenset()
    assert permission_updates == []


@pytest.mark.parametrize(
    "history_state, expected_status",
    [
        ("missing_history", "missing_history"),
        ("missing_event", "missing_event"),
        ("doing", "doing"),
        ("failure", "failure"),
        ("timeout", "timeout"),
        ("unknown", "unknown"),
        ("version_mismatch", "version_mismatch"),
    ],
)
def test_reconcile_blocks_deletion_until_data_plane_is_synced(history_state, expected_status, fake_gateway):
    _, _, release = make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(1, stage_name="prod", support_public=False, support_personal=False)],
    )
    data_plane = bind_data_plane(fake_gateway, "plane-1")
    to_delete = G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=99,
        bk_app_code="public",
        grant_type="oauth2_builtin",
        expires=NeverExpiresTime.time,
    )

    if history_state == "missing_event":
        G(
            ReleaseHistory,
            gateway=fake_gateway,
            stage=release.stage,
            resource_version=release.resource_version,
            data_plane=data_plane,
        )
    elif history_state != "missing_history":
        event_status = {
            "doing": PublishEventStatusEnum.DOING.value,
            "failure": PublishEventStatusEnum.FAILURE.value,
            "timeout": PublishEventStatusEnum.DOING.value,
            "unknown": "unknown",
            "version_mismatch": PublishEventStatusEnum.SUCCESS.value,
        }[history_state]
        history_version = release.resource_version
        if history_state == "version_mismatch":
            history_version = make_resource_version(fake_gateway, "0.9.0", [])
        _, event = make_history_event(
            release,
            data_plane,
            event_status,
            resource_version=history_version,
        )
        if history_state == "timeout":
            PublishEvent.objects.filter(id=event.id).update(created_time=timezone.now() - timedelta(minutes=11))

    result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway)

    assert result.deletion_blocked is True
    assert len(result.blockers) == 1
    assert result.blockers[0].status == expected_status
    assert AppResourcePermission.objects.filter(id=to_delete.id).exists()


def test_reconcile_requires_every_active_data_plane_and_deletes_after_success(fake_gateway):
    _, _, release = make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(1, stage_name="prod", support_public=False, support_personal=False)],
    )
    plane_1 = bind_data_plane(fake_gateway, "plane-1")
    plane_2 = bind_data_plane(fake_gateway, "plane-2")
    make_history_event(release, plane_1, PublishEventStatusEnum.SUCCESS.value)
    make_history_event(release, plane_2, PublishEventStatusEnum.DOING.value)
    to_delete = G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=99,
        bk_app_code="personal",
        grant_type="oauth2_builtin",
        expires=NeverExpiresTime.time,
    )

    blocked = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway)
    assert blocked.deletion_blocked is True
    assert {blocker.data_plane_name for blocker in blocked.blockers} == {"plane-2"}
    assert AppResourcePermission.objects.filter(id=to_delete.id).exists()

    make_history_event(release, plane_2, PublishEventStatusEnum.SUCCESS.value)
    synced = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway)
    assert synced.deletion_blocked is False
    assert synced.blockers == ()
    assert not AppResourcePermission.objects.filter(id=to_delete.id).exists()


def test_inactive_stage_must_be_synced_before_permission_cleanup(fake_gateway):
    _, _, release = make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(1, stage_name="prod", support_public=True, support_personal=False)],
        active=False,
    )
    data_plane = bind_data_plane(fake_gateway, "plane-1")
    make_history_event(release, data_plane, PublishEventStatusEnum.FAILURE.value)
    to_delete = G(
        AppResourcePermission,
        gateway=fake_gateway,
        resource_id=1,
        bk_app_code="public",
        grant_type="oauth2_builtin",
        expires=NeverExpiresTime.time,
    )

    blocked = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway)
    assert blocked.desired == frozenset()
    assert blocked.deletion_blocked is True
    assert AppResourcePermission.objects.filter(id=to_delete.id).exists()

    make_history_event(release, data_plane, PublishEventStatusEnum.SUCCESS.value)
    synced = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway)
    assert synced.deletion_blocked is False
    assert not AppResourcePermission.objects.filter(id=to_delete.id).exists()


def test_inactive_gateway_has_empty_desired_permissions(fake_gateway):
    make_stage_release(
        fake_gateway,
        "prod",
        "1.0.0",
        [make_resource_snapshot(1, stage_name="prod", support_public=True, support_personal=True)],
    )
    fake_gateway.status = GatewayStatusEnum.INACTIVE.value
    fake_gateway.save(update_fields=["status"])

    result = OAuth2BuiltinPermissionReconciler().reconcile_gateway(fake_gateway, apply=False)

    assert result.desired == frozenset()
