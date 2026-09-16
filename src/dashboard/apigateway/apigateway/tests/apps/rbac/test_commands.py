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
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from django_dynamic_fixture import G

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.iam_context import GatewayIAMSyncContext
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.iam import GatewayIAMModelSyncResult, GatewayIAMSyncItem, GatewayIAMSyncResult
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


def test_check_gateway_rbac_data_succeeds(fake_gateway):
    GatewayMember.objects.filter(gateway=fake_gateway).update(expires=timezone.now() - timedelta(days=1))

    call_command("check_gateway_rbac_data")


def test_check_gateway_rbac_data_rejects_empty_gateway():
    G(Gateway)

    with pytest.raises(CommandError):
        call_command("check_gateway_rbac_data")


def test_check_gateway_rbac_data_rejects_gateway_without_administrator():
    gateway = G(Gateway)
    G(
        GatewayMember,
        gateway=gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    with pytest.raises(CommandError):
        call_command("check_gateway_rbac_data")


@pytest.mark.parametrize(
    "username, role",
    [
        ("member", "invalid"),
        ("", GatewayRoleEnum.ADMINISTRATOR.value),
        (" ", GatewayRoleEnum.ADMINISTRATOR.value),
        (" member ", GatewayRoleEnum.ADMINISTRATOR.value),
        ("member ", GatewayRoleEnum.ADMINISTRATOR.value),
    ],
)
def test_check_gateway_rbac_data_rejects_invalid_member(fake_gateway, username, role):
    GatewayMember.objects.create(
        gateway=fake_gateway,
        username=username,
        role=role,
    )

    with pytest.raises(CommandError):
        call_command("check_gateway_rbac_data")


def test_sync_gateway_rbac_model_to_iam_skips_when_disabled(settings, mocker):
    settings.BK_IAM_V4_ENABLED = False
    syncer = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_model_to_iam.GatewayIAMModelSyncer"
    )
    output = StringIO()

    call_command("sync_gateway_rbac_model_to_iam", stdout=output)

    assert output.getvalue() == "BK_IAM_V4_ENABLED=false; skipped\n"
    syncer.assert_not_called()


def test_sync_gateway_rbac_model_to_iam_reports_deterministic_counts(settings, mocker):
    settings.BK_IAM_V4_ENABLED = True
    settings.BK_IAM_V4_API_URL = "https://bkiam.example.com"
    settings.BK_IAM_V4_MANAGERS = ["admin"]
    sync = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_model_to_iam.GatewayIAMModelSyncer"
    ).return_value.sync
    sync.return_value = GatewayIAMModelSyncResult(
        created=2,
        updated=3,
        unchanged=4,
    )
    output = StringIO()

    call_command("sync_gateway_rbac_model_to_iam", stdout=output)

    assert output.getvalue() == "created=2 updated=3 unchanged=4\n"


def test_sync_gateway_rbac_model_to_iam_converts_failure_to_command_error(settings, mocker):
    settings.BK_IAM_V4_ENABLED = True
    settings.BK_IAM_V4_API_URL = "https://bkiam.example.com"
    settings.BK_IAM_V4_MANAGERS = ["admin"]
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_model_to_iam.GatewayIAMModelSyncer"
    ).return_value.sync.side_effect = RuntimeError("IAM unavailable")

    with pytest.raises(CommandError, match="IAM unavailable"):
        call_command("sync_gateway_rbac_model_to_iam")


def _enable_iam(settings):
    settings.BK_IAM_V4_ENABLED = True
    settings.BK_IAM_V4_API_URL = "https://bkiam.example.com"
    settings.BK_IAM_V4_MANAGERS = ["admin"]


def _sync_result(gateway, *, applied=False, grant_count=0):
    return GatewayIAMSyncResult(
        gateway_id=gateway.id,
        gateway_name=gateway.name,
        grants=tuple(
            GatewayIAMSyncItem(
                username=f"user-{index}",
                role=GatewayRoleEnum.OPERATOR.value,
                expired_at=1_900_000_000,
                reason="missing",
            )
            for index in range(grant_count)
        ),
        revokes=(),
        unchanged=1,
        applied=applied,
    )


def test_sync_gateway_rbac_auth_to_iam_skips_when_disabled(settings, mocker):
    settings.BK_IAM_V4_ENABLED = False
    synchronizer = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    )
    output = StringIO()

    call_command("sync_gateway_rbac_auth_to_iam", stdout=output)

    assert output.getvalue() == "BK_IAM_V4_ENABLED=false; skipped\n"
    synchronizer.assert_not_called()


@pytest.mark.parametrize(
    "options",
    [
        {},
        {"gateway": "one", "all": True},
        {"gateway": "one", "username": "alice"},
        {"username": "alice", "all": True},
    ],
)
def test_sync_gateway_rbac_auth_to_iam_rejects_argument_conflicts(settings, options):
    _enable_iam(settings)

    with pytest.raises(CommandError):
        call_command("sync_gateway_rbac_auth_to_iam", **options)


@pytest.mark.parametrize(
    "options",
    [
        {"initial": True, "all": True},
        {"initial": True, "gateway": "one", "apply": True},
        {"initial": True, "username": "alice", "apply": True},
    ],
)
def test_sync_gateway_rbac_auth_to_iam_rejects_invalid_initial_options(settings, options):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="--initial 必须与 --all --apply 配合使用"):
        call_command("sync_gateway_rbac_auth_to_iam", **options)


@pytest.mark.parametrize("page_size", [0, 101])
def test_sync_gateway_rbac_auth_to_iam_rejects_invalid_page_size(settings, page_size):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="1 到 100"):
        call_command("sync_gateway_rbac_auth_to_iam", all=True, page_size=page_size)


def test_sync_gateway_rbac_auth_to_iam_rejects_negative_gateway_delay(settings):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="--gateway-delay"):
        call_command("sync_gateway_rbac_auth_to_iam", all=True, gateway_delay=-0.1)


@pytest.mark.parametrize("selector", ["id", "name"])
def test_sync_gateway_rbac_auth_to_iam_accepts_gateway_id_or_name(
    settings,
    mocker,
    fake_gateway,
    selector,
):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway)

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        gateway=str(fake_gateway.id) if selector == "id" else fake_gateway.name,
    )

    reconcile.assert_called_once_with(
        fake_gateway.id,
        apply=False,
        operator="admin",
        username=None,
    )


def test_sync_gateway_rbac_auth_to_iam_username_checks_every_gateway(settings, mocker, fake_gateway):
    _enable_iam(settings)
    second_gateway = G(Gateway)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = [_sync_result(gateway) for gateway in Gateway.objects.order_by("id")]

    call_command("sync_gateway_rbac_auth_to_iam", username="alice")

    assert [call.args[0] for call in reconcile.call_args_list] == sorted([fake_gateway.id, second_gateway.id])
    assert all(call.kwargs["username"] == "alice" for call in reconcile.call_args_list)


def test_sync_gateway_rbac_auth_to_iam_rate_limits_between_gateways(settings, mocker, fake_gateway):
    _enable_iam(settings)
    second_gateway = G(Gateway)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = [_sync_result(gateway) for gateway in Gateway.objects.order_by("id")]
    sleep = mocker.patch("apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.time.sleep")

    call_command("sync_gateway_rbac_auth_to_iam", all=True, gateway_delay=0.25)

    assert reconcile.call_count == 2
    sleep.assert_called_once_with(0.25)


def test_sync_gateway_rbac_auth_to_iam_threshold_rejects_before_apply(settings, mocker, fake_gateway):
    _enable_iam(settings)
    second_gateway = G(Gateway)
    gateways = list(Gateway.objects.order_by("id"))
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = [_sync_result(gateway, grant_count=1) for gateway in gateways]

    with pytest.raises(CommandError, match="超过 --max-changes=1"):
        call_command(
            "sync_gateway_rbac_auth_to_iam",
            all=True,
            apply=True,
            max_changes=1,
        )

    assert [call.args[0] for call in reconcile.call_args_list] == sorted([fake_gateway.id, second_gateway.id])
    assert all(call.kwargs["apply"] is False for call in reconcile.call_args_list)


def test_sync_gateway_rbac_auth_to_iam_threshold_rejection_makes_no_iam_writes(settings, mocker, fake_gateway):
    _enable_iam(settings)
    mocker.patch(
        "apigateway.biz.iam.sync.iter_authorization_subjects",
        return_value=iter([]),
    )
    add = mocker.patch("apigateway.biz.iam.sync.add_authorization")
    revoke = mocker.patch("apigateway.biz.iam.sync.revoke_authorization")

    with pytest.raises(CommandError, match="超过 --max-changes=0"):
        call_command(
            "sync_gateway_rbac_auth_to_iam",
            gateway=str(fake_gateway.id),
            apply=True,
            max_changes=0,
        )

    add.assert_not_called()
    revoke.assert_not_called()


def test_sync_gateway_rbac_auth_to_iam_force_applies_over_threshold(settings, mocker, fake_gateway):
    _enable_iam(settings)
    mocker.patch(
        "apigateway.biz.iam.sync.iter_authorization_subjects",
        return_value=iter([]),
    )
    add = mocker.patch("apigateway.biz.iam.sync.add_authorization")

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        gateway=str(fake_gateway.id),
        apply=True,
        max_changes=0,
        force=True,
    )

    add.assert_called_once()


def test_sync_gateway_rbac_auth_to_iam_all_apply_runs_on_every_invocation(settings, mocker, fake_gateway):
    _enable_iam(settings)
    GatewayIAMSyncContext().mark_initial_sync_completed()
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway)

    for _ in range(2):
        call_command("sync_gateway_rbac_auth_to_iam", all=True, apply=True, force=True, gateway_delay=0)

    assert [call.kwargs["apply"] for call in reconcile.call_args_list] == [False, True, False, True]


def test_sync_gateway_rbac_auth_to_iam_apply_failure_raises_command_error(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = RuntimeError("IAM unavailable")

    with pytest.raises(CommandError, match="IAM unavailable"):
        call_command("sync_gateway_rbac_auth_to_iam", all=True, apply=True, force=True, gateway_delay=0)


def test_sync_gateway_rbac_auth_to_iam_initial_marks_completion_after_success(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway)

    call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, force=True, gateway_delay=0)

    assert GatewayIAMSyncContext().is_initial_sync_completed()
    assert [call.kwargs["apply"] for call in reconcile.call_args_list] == [False, True]


def test_sync_gateway_rbac_auth_to_iam_initial_failure_does_not_mark_completion(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = RuntimeError("IAM unavailable")

    with pytest.raises(CommandError, match="IAM unavailable"):
        call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, force=True, gateway_delay=0)

    assert not GatewayIAMSyncContext().is_initial_sync_completed()


def test_sync_gateway_rbac_auth_to_iam_initial_skips_after_completion(settings, mocker):
    _enable_iam(settings)
    GatewayIAMSyncContext().mark_initial_sync_completed()
    synchronizer = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    )
    output = StringIO()

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        initial=True,
        all=True,
        apply=True,
        force=True,
        stdout=output,
    )

    assert output.getvalue() == "gateway RBAC initial sync already completed; skipped\n"
    synchronizer.assert_not_called()
