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
    assert {event.publish_id for event in events} == {fake_release_history.id, plane_history.id}
    assert len(events) == 2
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
