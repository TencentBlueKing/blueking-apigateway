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
from datetime import UTC, datetime, timedelta

import pytest
from celery.schedules import crontab
from django_dynamic_fixture import G

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.apps.rbac.tasks import (
    _renew_gateway_member_iam_authorizations,
    renew_gateway_member_iam_authorizations,
)
from apigateway.conf.celery_conf import CELERY_BEAT_SCHEDULE, CELERY_IMPORTS
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 9, 10, 8, 0, tzinfo=UTC)


@pytest.fixture(autouse=True)
def iam_v4_enabled(settings):
    settings.BK_IAM_V4_ENABLED = True
    settings.BK_APP_CODE = "bk-apigateway"
    settings.BK_IAM_V4_MANAGERS = ["admin"]


@pytest.fixture(autouse=True)
def renewal_lock(mocker):
    lock = mocker.Mock()
    lock.acquire.return_value = True
    mocker.patch("apigateway.apps.rbac.tasks.get_default_redis_client")
    constructor = mocker.patch("apigateway.apps.rbac.tasks.redis_lock.Lock", return_value=lock)
    return lock, constructor


def _gateway_members(gateway, count, *, expires):
    members = [
        GatewayMember(
            gateway=gateway,
            username=f"user-{index:03d}",
            role=GatewayRoleEnum.OPERATOR.value,
            expires=expires,
        )
        for index in range(count)
    ]
    return GatewayMember.objects.bulk_create(members)


def test_disabled_task_makes_no_external_or_lock_calls(settings, renewal_lock, mocker):
    settings.BK_IAM_V4_ENABLED = False
    lock, constructor = renewal_lock
    add_authorization = mocker.patch("apigateway.apps.rbac.tasks.add_authorization")

    renew_gateway_member_iam_authorizations()

    constructor.assert_not_called()
    lock.acquire.assert_not_called()
    add_authorization.assert_not_called()


def test_renews_due_and_null_expiry_only_after_iam_success(mocker):
    gateway = G(Gateway)
    due = G(
        GatewayMember,
        gateway=gateway,
        username="due",
        role=GatewayRoleEnum.ADMINISTRATOR.value,
        expires=NOW + timedelta(days=30),
    )
    no_expiry = G(
        GatewayMember,
        gateway=gateway,
        username="no-expiry",
        role=GatewayRoleEnum.OPERATOR.value,
        expires=None,
    )
    not_due = G(
        GatewayMember,
        gateway=gateway,
        username="not-due",
        role=GatewayRoleEnum.OPERATOR.value,
        expires=NOW + timedelta(days=30, seconds=1),
    )
    mocker.patch("apigateway.apps.rbac.tasks.timezone.now", return_value=NOW)

    def assert_local_expiry_not_updated(_authorizations, _operator):
        due.refresh_from_db()
        no_expiry.refresh_from_db()
        assert due.expires == NOW + timedelta(days=30)
        assert no_expiry.expires is None

    add_authorization = mocker.patch(
        "apigateway.apps.rbac.tasks.add_authorization",
        side_effect=assert_local_expiry_not_updated,
    )

    renew_gateway_member_iam_authorizations()

    add_authorization.assert_called_once()
    authorizations, operator = add_authorization.call_args.args
    assert [authorization["subject"]["id"] for authorization in authorizations] == ["due", "no-expiry"]
    assert {authorization["expired_at"] for authorization in authorizations} == {
        int((NOW + timedelta(days=365)).timestamp())
    }
    assert operator == "admin"

    due.refresh_from_db()
    no_expiry.refresh_from_db()
    not_due.refresh_from_db()
    assert due.expires == NOW + timedelta(days=365)
    assert no_expiry.expires == NOW + timedelta(days=365)
    assert not_due.expires == NOW + timedelta(days=30, seconds=1)


def test_batches_authorizations_at_twenty(mocker):
    gateway = G(Gateway)
    _gateway_members(gateway, 21, expires=NOW)
    mocker.patch("apigateway.apps.rbac.tasks.timezone.now", return_value=NOW)
    add_authorization = mocker.patch("apigateway.apps.rbac.tasks.add_authorization")

    renew_gateway_member_iam_authorizations()

    assert [len(item.args[0]) for item in add_authorization.call_args_list] == [20, 1]
    assert all(item.args[1] == "admin" for item in add_authorization.call_args_list)


def test_failed_batch_is_unchanged_and_later_batch_continues(mocker):
    gateway = G(Gateway)
    _gateway_members(gateway, 41, expires=NOW)
    mocker.patch("apigateway.apps.rbac.tasks.timezone.now", return_value=NOW)
    add_authorization = mocker.patch(
        "apigateway.apps.rbac.tasks.add_authorization",
        side_effect=[None, RuntimeError("IAM unavailable"), None],
    )

    with pytest.raises(RuntimeError, match="failed to renew 1"):
        renew_gateway_member_iam_authorizations()

    assert len(add_authorization.call_args_list) == 3
    expiries = dict(
        GatewayMember.objects.filter(gateway=gateway).order_by("username").values_list("username", "expires")
    )
    renewed_expires = NOW + timedelta(days=365)
    assert all(expiries[f"user-{index:03d}"] == renewed_expires for index in range(20))
    assert all(expiries[f"user-{index:03d}"] == NOW for index in range(20, 40))
    assert expiries["user-040"] == renewed_expires


def test_lock_held_skips_cleanly(renewal_lock, mocker):
    lock, _constructor = renewal_lock
    lock.acquire.return_value = False
    member_filter = mocker.patch("apigateway.apps.rbac.tasks.GatewayMember.objects.filter")
    add_authorization = mocker.patch("apigateway.apps.rbac.tasks.add_authorization")

    renew_gateway_member_iam_authorizations()

    lock.acquire.assert_called_once_with(blocking=False)
    lock.release.assert_not_called()
    member_filter.assert_not_called()
    add_authorization.assert_not_called()


def test_gateway_row_is_locked_before_members_are_read_and_iam_is_written(mocker):
    gateway = G(Gateway)
    member = G(
        GatewayMember,
        gateway=gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
        expires=NOW,
    )
    events = []
    original_select_for_update = Gateway.objects.select_for_update
    original_filter = GatewayMember.objects.filter

    def select_for_update(*args, **kwargs):
        events.append("gateway-lock")
        return original_select_for_update(*args, **kwargs)

    def member_filter(*args, **kwargs):
        if kwargs.get("gateway_id") == gateway.id:
            events.append("member-read")
        return original_filter(*args, **kwargs)

    def add_authorization(_authorizations, _operator):
        events.append("iam-write")

    mocker.patch.object(Gateway.objects, "select_for_update", side_effect=select_for_update)
    mocker.patch.object(GatewayMember.objects, "filter", side_effect=member_filter)
    mocker.patch("apigateway.apps.rbac.tasks.add_authorization", side_effect=add_authorization)

    failed_batches = _renew_gateway_member_iam_authorizations(
        gateway.id,
        NOW + timedelta(days=30),
        NOW + timedelta(days=365),
    )

    assert failed_batches == 0
    assert events[:3] == ["gateway-lock", "member-read", "iam-write"]
    member.refresh_from_db()
    assert member.expires == NOW + timedelta(days=365)


def test_task_registration_and_daily_schedule():
    task_name = "apigateway.apps.rbac.tasks.renew_gateway_member_iam_authorizations"

    assert "apigateway.apps.rbac.tasks" in CELERY_IMPORTS
    assert CELERY_BEAT_SCHEDULE[task_name] == {
        "task": task_name,
        "schedule": crontab(day_of_week="*", hour=2, minute=10),
    }
