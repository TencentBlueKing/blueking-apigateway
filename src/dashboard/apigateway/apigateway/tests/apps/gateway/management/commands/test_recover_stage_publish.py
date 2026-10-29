#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关 (BlueKing - APIGateway) available.
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

from datetime import timedelta
from io import StringIO

import pytest
from ddf import G
from django.core.management import CommandError, call_command
from django.utils import timezone

from apigateway.apps.data_plane.models import DataPlane
from apigateway.core.models import Gateway, PublishEvent, ReleaseHistory, Stage
from apigateway.utils.exception import LockTimeout

pytestmark = pytest.mark.django_db
COMMAND = "recover_stage_publish"
MODULE = "apigateway.apps.gateway.management.commands.recover_stage_publish"


@pytest.fixture
def publish_lock(mocker):
    return mocker.patch(f"{MODULE}.Lock")


def test_preview_does_not_write(fake_gateway, fake_release_history):
    output = StringIO()
    call_command(COMMAND, gateway_id=fake_gateway.id, stdout=output)
    assert not PublishEvent.objects.exists()
    assert str(fake_release_history.id) in output.getvalue()
    assert "would_recover" in output.getvalue()


def test_apply_is_scoped_and_idempotent(fake_gateway, fake_stage, fake_release_history, publish_lock):
    old = timezone.now() - timedelta(days=400)
    other_stage = G(Stage, gateway=fake_gateway, name="other")
    ignored = G(ReleaseHistory, gateway=fake_gateway, stage=other_stage, created_time=old)
    other_gateway_history = G(ReleaseHistory, created_time=old)
    plane_history = G(
        ReleaseHistory, gateway=fake_gateway, stage=fake_stage, data_plane=G(DataPlane), created_time=old
    )
    args = {
        "gateway_id": fake_gateway.id,
        "stage": fake_stage.name,
        "apply": True,
        "operator": "operator",
        "reason": "missing events",
    }
    call_command(COMMAND, **args)
    call_command(COMMAND, **args)

    events = list(PublishEvent.objects.order_by("publish_id"))
    assert {event.publish_id for event in events} == {plane_history.id}
    assert len(events) == 1
    for event in events:
        assert event.status == "failure"
        assert event.gateway_id == fake_gateway.id
        assert event.stage_id == fake_stage.id
        assert event.created_by == "operator"
        assert event.detail["reason"] == "missing events"
        assert "unknown" in event.detail["err_msg"].lower()
    assert not PublishEvent.objects.filter(publish_id__in=[ignored.id, other_gateway_history.id]).exists()
    assert publish_lock.call_args.args == (f"{fake_gateway.id}_{fake_stage.id}",)


@pytest.mark.parametrize("existing_status", ["success", "doing", "pending", "failure", None])
def test_skips_existing_events_and_recent_histories(fake_gateway, fake_release_history, publish_lock, existing_status):
    if existing_status:
        G(PublishEvent, publish=fake_release_history, status=existing_status)
    else:
        ReleaseHistory.objects.filter(pk=fake_release_history.pk).update(created_time=timezone.now())
    before = list(PublishEvent.objects.values())
    output = StringIO()
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair", stdout=output)
    assert list(PublishEvent.objects.values()) == before
    assert "skipped" in output.getvalue()


@pytest.mark.parametrize("change", ["new_history", "new_event"])
def test_rechecks_after_acquiring_lock(fake_gateway, fake_stage, fake_release_history, publish_lock, change):
    def concurrent_publish():
        if change == "new_history":
            G(ReleaseHistory, gateway=fake_gateway, stage=fake_stage)
        else:
            G(PublishEvent, publish=fake_release_history, status="success", name="load_configuration", step=5)

    publish_lock.return_value.__enter__.side_effect = concurrent_publish
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert not PublishEvent.objects.filter(status="failure").exists()


def test_lock_failure_does_not_write(fake_gateway, fake_release_history, publish_lock):
    publish_lock.return_value.__enter__.side_effect = LockTimeout("busy")
    with pytest.raises(CommandError, match="lock"):
        call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert not PublishEvent.objects.exists()


@pytest.mark.parametrize("options", [{}, {"operator": "operator"}, {"operator": "x" * 33, "reason": "repair"}])
def test_apply_requires_audit_metadata(fake_gateway, fake_release_history, options):
    with pytest.raises(CommandError):
        call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, **options)
    assert not PublishEvent.objects.exists()


def test_stage_must_belong_to_gateway(fake_gateway):
    G(Stage, gateway=G(Gateway), name="foreign")
    with pytest.raises(CommandError):
        call_command(COMMAND, gateway_id=fake_gateway.id, stage="foreign")


@pytest.mark.parametrize("age", [600, 601, None])
def test_recovery_timeout_boundary(fake_gateway, fake_release_history, publish_lock, mocker, age):
    now = timezone.now()
    mocker.patch("django.utils.timezone.now", return_value=now)
    created_time = now - timedelta(seconds=age) if age is not None else None
    ReleaseHistory.objects.filter(pk=fake_release_history.pk).update(created_time=created_time)
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert PublishEvent.objects.filter(publish_id=fake_release_history.id).exists() == (age == 601)


def test_only_latest_publish_is_recovered(fake_gateway, fake_stage, fake_release_history, publish_lock):
    latest = G(
        ReleaseHistory, gateway=fake_gateway, stage=fake_stage, created_time=timezone.now() - timedelta(days=400)
    )
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert list(PublishEvent.objects.values_list("publish_id", flat=True)) == [latest.id]


def test_gateway_without_history(fake_gateway, fake_stage):
    output = StringIO()
    call_command(COMMAND, gateway_id=fake_gateway.id, stdout=output)
    assert "no publish history" in output.getvalue()
    assert not PublishEvent.objects.exists()


def test_missing_gateway():
    with pytest.raises(CommandError, match="Gateway does not exist"):
        call_command(COMMAND, gateway_id=99999)


@pytest.mark.parametrize("gateway_option", ["--gateway_name", "--gateawy_name"])
@pytest.mark.parametrize("stage_option", ["--stage_name", "--stage"])
def test_name_options_are_scoped(
    fake_gateway, fake_stage, fake_release_history, publish_lock, gateway_option, stage_option
):
    foreign_gateway = G(Gateway)
    foreign_stage = G(Stage, gateway=foreign_gateway, name=fake_stage.name)
    G(ReleaseHistory, gateway=foreign_gateway, stage=foreign_stage, created_time=fake_release_history.created_time)
    other_stage = G(Stage, gateway=fake_gateway)
    G(ReleaseHistory, gateway=fake_gateway, stage=other_stage, created_time=fake_release_history.created_time)

    call_command(
        COMMAND,
        gateway_option,
        fake_gateway.name,
        stage_option,
        fake_stage.name,
        "--apply",
        "--operator",
        "operator",
        "--reason",
        "missing events",
    )

    assert list(PublishEvent.objects.values_list("publish_id", flat=True)) == [fake_release_history.id]


def test_name_options_preview(fake_gateway, fake_stage, fake_release_history):
    output = StringIO()
    call_command(COMMAND, gateway_name=fake_gateway.name, stage_name=fake_stage.name, stdout=output)
    assert "would_recover" in output.getvalue()
    assert fake_gateway.name in output.getvalue()
    assert not PublishEvent.objects.exists()


@pytest.mark.parametrize(
    "options",
    [{"gateway_name": ""}, {"gateway_name": " "}, {"stage_name": ""}, {"stage_name": " "}, {"gateway_id": 1}],
)
def test_invalid_selectors_do_not_broaden_scope(fake_gateway, fake_release_history, options):
    selectors = {"gateway_name": fake_gateway.name, **options}
    with pytest.raises(CommandError):
        call_command(COMMAND, apply=True, operator="operator", reason="repair", **selectors)
    assert not PublishEvent.objects.exists()


def test_missing_gateway_name():
    with pytest.raises(CommandError, match="Gateway does not exist"):
        call_command(COMMAND, gateway_name="does-not-exist")


def test_all_stages_only_recovers_eligible_latest_histories(
    fake_gateway, fake_stage, fake_release_history, publish_lock
):
    old = timezone.now() - timedelta(days=400)
    eligible_stage = G(Stage, gateway=fake_gateway, name="eligible")
    eligible = G(ReleaseHistory, gateway=fake_gateway, stage=eligible_stage, created_time=old)
    G(Stage, gateway=fake_gateway, name="unpublished")
    for status in ["success", "doing", "pending", "failure"]:
        stage = G(Stage, gateway=fake_gateway, name=status)
        G(ReleaseHistory, gateway=fake_gateway, stage=stage, created_time=old)
        latest = G(ReleaseHistory, gateway=fake_gateway, stage=stage, created_time=old)
        G(PublishEvent, gateway=fake_gateway, stage=stage, publish=latest, status=status)
    for age in [0, None]:
        stage = G(Stage, gateway=fake_gateway)
        G(ReleaseHistory, gateway=fake_gateway, stage=stage, created_time=old)
        G(ReleaseHistory, gateway=fake_gateway, stage=stage, created_time=timezone.now() if age == 0 else None)
    foreign_gateway = G(Gateway)
    foreign_stage = G(Stage, gateway=foreign_gateway, name=fake_stage.name)
    G(ReleaseHistory, gateway=foreign_gateway, stage=foreign_stage, created_time=old)
    before = list(PublishEvent.objects.order_by("id").values())
    output = StringIO()

    for _ in range(2):
        call_command(
            COMMAND, gateway_name=fake_gateway.name, apply=True, operator="operator", reason="repair", stdout=output
        )

    assert list(PublishEvent.objects.order_by("id").values())[: len(before)] == before
    repaired = PublishEvent.objects.exclude(id__in=[event["id"] for event in before])
    assert set(repaired.values_list("publish_id", flat=True)) == {fake_release_history.id, eligible.id}
    assert repaired.count() == 2
    assert "no publish history" in output.getvalue()


def test_older_data_plane_history_is_not_recovered(fake_gateway, fake_stage, fake_release_history, publish_lock):
    latest = G(
        ReleaseHistory,
        gateway=fake_gateway,
        stage=fake_stage,
        data_plane=G(DataPlane),
        created_time=fake_release_history.created_time,
    )
    G(PublishEvent, gateway=fake_gateway, stage=fake_stage, publish=latest, status="success")
    before = list(PublishEvent.objects.values())
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert list(PublishEvent.objects.values()) == before


def test_rechecks_new_publish_on_another_data_plane(fake_gateway, fake_stage, fake_release_history, publish_lock):
    def concurrent_publish():
        G(ReleaseHistory, gateway=fake_gateway, stage=fake_stage, data_plane=G(DataPlane))

    publish_lock.return_value.__enter__.side_effect = concurrent_publish
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert not PublishEvent.objects.exists()


def test_inconsistent_history_gateway_is_not_recovered(fake_gateway, fake_stage, fake_release_history, publish_lock):
    G(ReleaseHistory, gateway=G(Gateway), stage=fake_stage, created_time=fake_release_history.created_time)
    call_command(COMMAND, gateway_id=fake_gateway.id, apply=True, operator="operator", reason="repair")
    assert not PublishEvent.objects.exists()
