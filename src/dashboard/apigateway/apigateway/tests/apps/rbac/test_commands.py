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
from types import SimpleNamespace

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.utils import timezone
from django_dynamic_fixture import G

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.iam_context import GatewayIAMSyncContext
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.iam import GatewayIAMModelSyncResult, GatewayIAMSyncItem, GatewayIAMSyncResult
from apigateway.biz.iam.constants import BK_IAM_V4_SYSTEM_ID
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
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_model_to_iam.GatewayIAMModelSyncer"
    ).return_value.sync.side_effect = RuntimeError("IAM unavailable")

    with pytest.raises(CommandError, match="IAM unavailable"):
        call_command("sync_gateway_rbac_model_to_iam")


def _enable_iam(settings):
    settings.BK_IAM_V4_ENABLED = True


def _sync_result(gateway, *, applied=False, grant_count=0):
    return GatewayIAMSyncResult(
        gateway_id=gateway.id,
        gateway_name=gateway.name,
        grants=tuple(
            GatewayIAMSyncItem(
                username=f"user-{index}",
                role=GatewayRoleEnum.OPERATOR.value,
                expired_at=1_900_000_000,
                reason="missing-in-iam",
            )
            for index in range(grant_count)
        ),
        revokes=(),
        unchanged=1,
        applied=applied,
    )


def test_sync_gateway_rbac_auth_to_iam_skips_when_disabled(settings, mocker):
    settings.BK_IAM_V4_ENABLED = False
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.uuid.uuid4",
        return_value=SimpleNamespace(hex="run-disabled"),
    )
    synchronizer = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    )
    output = StringIO()

    call_command("sync_gateway_rbac_auth_to_iam", stdout=output)

    assert output.getvalue() == (
        "event=iam-rbac-sync-summary run_id=run-disabled status=skipped reason=iam-disabled\n"
    )
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
        operator=BK_IAM_V4_SYSTEM_ID,
        username=None,
    )


def test_sync_gateway_rbac_auth_to_iam_explicit_dry_run_does_not_apply(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway)

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        gateway=str(fake_gateway.id),
        dry_run=True,
    )

    reconcile.assert_called_once_with(
        fake_gateway.id,
        apply=False,
        operator=BK_IAM_V4_SYSTEM_ID,
        username=None,
    )


def test_sync_gateway_rbac_auth_to_iam_rejects_apply_with_dry_run(settings, fake_gateway):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="不能同时指定"):
        call_command(
            "sync_gateway_rbac_auth_to_iam",
            gateway=str(fake_gateway.id),
            apply=True,
            dry_run=True,
        )


def test_sync_gateway_rbac_auth_to_iam_reports_one_readable_line_per_gateway(settings, mocker, fake_gateway):
    _enable_iam(settings)
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.time.monotonic",
        return_value=100,
    )
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.uuid.uuid4",
        return_value=SimpleNamespace(hex="run-readable"),
    )
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway, grant_count=1)
    output = StringIO()

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        gateway=str(fake_gateway.id),
        stdout=output,
    )

    gateway_lines = [line for line in output.getvalue().splitlines() if "event=iam-rbac-sync-gateway" in line]
    assert gateway_lines == [
        f"event=iam-rbac-sync-gateway run_id=run-readable mode=dry-run gateway_index=1 gateways_total=1 "
        f"status=success outcome=changed gateway_id={fake_gateway.id} gateway_name={fake_gateway.name} "
        "grants_planned=1 revokes_planned=0 already_consistent=1 "
        'changes="grant(username=user-0,role=operator,reason=missing-in-iam,'
        'expires_at=2030-03-17T17:46:40Z)" changes_logged=1 changes_omitted=0 duration_ms=0'
    ]


def test_sync_gateway_rbac_auth_to_iam_limits_logged_changes(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway, grant_count=25)
    output = StringIO()

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        gateway=str(fake_gateway.id),
        stdout=output,
    )

    gateway_line = next(line for line in output.getvalue().splitlines() if "event=iam-rbac-sync-gateway" in line)
    assert "changes_logged=20 changes_omitted=5" in gateway_line


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


def test_sync_gateway_rbac_auth_to_iam_apply_reconciles_each_gateway_once(settings, mocker, fake_gateway):
    _enable_iam(settings)
    second_gateway = G(Gateway)
    gateways = list(Gateway.objects.order_by("id"))
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = [_sync_result(gateway, applied=True, grant_count=1) for gateway in gateways]

    call_command("sync_gateway_rbac_auth_to_iam", all=True, apply=True, gateway_delay=0)

    assert [call.args[0] for call in reconcile.call_args_list] == sorted([fake_gateway.id, second_gateway.id])
    assert all(call.kwargs["apply"] is True for call in reconcile.call_args_list)


def test_sync_gateway_rbac_auth_to_iam_apply_writes_iam_without_preflight(settings, mocker, fake_gateway):
    _enable_iam(settings)
    mocker.patch(
        "apigateway.biz.iam.authorization.iter_authorization_subjects",
        return_value=iter([]),
    )
    add = mocker.patch("apigateway.biz.iam.authorization.add_authorization")
    revoke = mocker.patch("apigateway.biz.iam.authorization.revoke_authorization")

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        gateway=str(fake_gateway.id),
        apply=True,
    )

    add.assert_called_once()
    revoke.assert_not_called()


def test_sync_gateway_rbac_auth_to_iam_all_apply_runs_on_every_invocation(settings, mocker, fake_gateway):
    _enable_iam(settings)
    GatewayIAMSyncContext().mark_initial_sync_completed()
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway)

    for _ in range(2):
        call_command("sync_gateway_rbac_auth_to_iam", all=True, apply=True, gateway_delay=0)

    assert [call.kwargs["apply"] for call in reconcile.call_args_list] == [True, True]


def test_sync_gateway_rbac_auth_to_iam_apply_failure_raises_command_error(settings, mocker, fake_gateway):
    _enable_iam(settings)
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.uuid.uuid4",
        return_value=SimpleNamespace(hex="run-failed"),
    )
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = RuntimeError("IAM unavailable")
    output = StringIO()
    error_output = StringIO()

    with pytest.raises(CommandError, match="1/1 个网关失败; run_id=run-failed"):
        call_command(
            "sync_gateway_rbac_auth_to_iam",
            all=True,
            apply=True,
            gateway_delay=0,
            stdout=output,
            stderr=error_output,
        )

    failure_line = error_output.getvalue()
    assert (
        "event=iam-rbac-sync-gateway run_id=run-failed mode=apply gateway_index=1 gateways_total=1 status=failed"
    ) in failure_line
    assert f"gateway_id={fake_gateway.id} gateway_name={fake_gateway.name}" in failure_line
    assert 'write_result=unknown error="IAM unavailable"' in failure_line
    assert (
        "event=iam-rbac-sync-summary run_id=run-failed mode=apply status=failed gateways_total=1 "
        "gateways_succeeded=0 gateways_failed=1 grants_processed=0 revokes_processed=0 "
        "already_consistent=0 failed_gateway_changes=unknown"
    ) in output.getvalue()


def test_sync_gateway_rbac_auth_to_iam_initial_marks_completion_after_success(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(fake_gateway)

    call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, gateway_delay=0)

    assert GatewayIAMSyncContext().is_initial_sync_completed()
    assert [call.kwargs["apply"] for call in reconcile.call_args_list] == [True]


def test_sync_gateway_rbac_auth_to_iam_initial_failure_does_not_mark_completion(settings, mocker, fake_gateway):
    _enable_iam(settings)
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.side_effect = RuntimeError("IAM unavailable")

    with pytest.raises(CommandError, match="1/1 个网关失败"):
        call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, gateway_delay=0)

    assert not GatewayIAMSyncContext().is_initial_sync_completed()


def test_sync_gateway_rbac_auth_to_iam_initial_skips_after_completion(settings, mocker):
    _enable_iam(settings)
    GatewayIAMSyncContext().mark_initial_sync_completed()
    mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.uuid.uuid4",
        return_value=SimpleNamespace(hex="run-complete"),
    )
    synchronizer = mocker.patch(
        "apigateway.apps.rbac.management.commands.sync_gateway_rbac_auth_to_iam.GatewayIAMAuthorizationSynchronizer"
    )
    output = StringIO()

    call_command(
        "sync_gateway_rbac_auth_to_iam",
        initial=True,
        all=True,
        apply=True,
        stdout=output,
    )

    assert output.getvalue() == (
        "event=iam-rbac-sync-summary run_id=run-complete mode=apply status=skipped "
        "reason=initial-sync-already-completed\n"
    )
    synchronizer.assert_not_called()


def test_add_global_gateway_administrators_apply_succeeds_when_iam_disabled(settings, mocker):
    settings.BK_IAM_V4_ENABLED = False
    gateway = G(Gateway, tenant_mode="global", tenant_id="")
    apply_iam = mocker.patch("apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam")
    synchronizer = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.GatewayIAMAuthorizationSynchronizer"
    )
    output = StringIO()

    call_command("add_global_gateway_administrators", username=["alice"], apply=True, stdout=output)
    assert GatewayMember.objects.is_gateway_administrator(gateway.id, "alice")
    apply_iam.assert_not_called()
    synchronizer.assert_not_called()
    assert "iam_enabled=false" in output.getvalue()
    assert "iam_skipped=true" in output.getvalue()


def test_add_global_gateway_administrators_dry_run_only_plans_global_gateways(settings, mocker):
    _enable_iam(settings)
    global_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    single_gateway = G(Gateway, tenant_mode="single", tenant_id="default")
    add_administrators = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.add_gateway_administrators"
    )
    synchronizer = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.GatewayIAMAuthorizationSynchronizer"
    )
    output = StringIO()

    call_command("add_global_gateway_administrators", username=["alice"], stdout=output)

    add_administrators.assert_not_called()
    synchronizer.assert_not_called()
    assert (
        f"gateway={global_gateway.id}:{global_gateway.name} local_change=true administrators=['alice'] apply=false"
    ) in output.getvalue()
    assert f"gateway={single_gateway.id}:{single_gateway.name}" not in output.getvalue()


def test_add_global_gateway_administrators_gateway_name_selector_limits_to_one_global_gateway(settings, mocker):
    _enable_iam(settings)
    target_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    other_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    output = StringIO()

    call_command(
        "add_global_gateway_administrators",
        username=["alice"],
        gateway_name=[target_gateway.name],
        stdout=output,
    )

    assert f"gateway={target_gateway.id}:{target_gateway.name}" in output.getvalue()
    assert f"gateway={other_gateway.id}:{other_gateway.name}" not in output.getvalue()


def test_add_global_gateway_administrators_gateway_name_selector_accepts_comma_separated_values(settings):
    _enable_iam(settings)
    target_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    second_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    other_gateway = G(Gateway, tenant_mode="global", tenant_id="")
    output = StringIO()

    call_command(
        "add_global_gateway_administrators",
        "--username",
        "alice",
        "--gateway-name",
        f"{target_gateway.name}, {second_gateway.name}",
        "--gateway-name",
        target_gateway.name,
        stdout=output,
    )

    assert f"gateway={target_gateway.id}:{target_gateway.name}" in output.getvalue()
    assert f"gateway={second_gateway.id}:{second_gateway.name}" in output.getvalue()
    assert f"gateway={other_gateway.id}:{other_gateway.name}" not in output.getvalue()


def test_add_global_gateway_administrators_gateway_name_selector_rejects_non_global_gateway(settings):
    _enable_iam(settings)
    gateway = G(Gateway, tenant_mode="single", tenant_id="default")

    with pytest.raises(CommandError, match=f"global 网关不存在: {gateway.name}"):
        call_command("add_global_gateway_administrators", username=["alice"], gateway_name=[gateway.name])


def test_add_global_gateway_administrators_gateway_name_selector_rejects_empty_name(settings):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="--gateway-name 不能为空"):
        call_command("add_global_gateway_administrators", gateway_name=["one,,two"], username=["alice"])


def test_add_global_gateway_administrators_apply_processes_all_global_gateways(settings, mocker):
    _enable_iam(settings)
    active_gateway = G(Gateway, tenant_mode="global", tenant_id="", status=1)
    inactive_gateway = G(Gateway, tenant_mode="global", tenant_id="", status=0)
    add_administrators = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.add_gateway_administrators",
        return_value=["alice"],
    )
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(active_gateway, applied=True)
    output = StringIO()

    call_command(
        "add_global_gateway_administrators",
        username=["alice"],
        apply=True,
        stdout=output,
    )

    assert add_administrators.call_args_list == [
        mocker.call(active_gateway, ["alice"], "admin"),
        mocker.call(inactive_gateway, ["alice"], "admin"),
    ]
    reconcile.assert_not_called()
    assert "summary gateways=2 planned=2 applied=2 unchanged=0 failed=0\n" in output.getvalue()


def test_add_global_gateway_administrators_writes_local_member_and_iam(settings, mocker):
    _enable_iam(settings)
    gateway = G(Gateway, tenant_mode="global", tenant_id="")
    apply_iam = mocker.patch("apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam")
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(gateway, applied=True)

    call_command("add_global_gateway_administrators", username=["alice"], apply=True)

    assert GatewayMember.objects.is_gateway_administrator(gateway.id, "alice")
    apply_iam.assert_called_once()
    reconcile.assert_not_called()


def test_add_global_gateway_administrators_reconciles_existing_local_member(settings, mocker):
    _enable_iam(settings)
    gateway = G(Gateway, tenant_mode="global", tenant_id="")
    G(
        GatewayMember,
        gateway=gateway,
        username="alice",
        role=GatewayRoleEnum.ADMINISTRATOR.value,
    )
    reconcile = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.GatewayIAMAuthorizationSynchronizer"
    ).return_value.reconcile_gateway
    reconcile.return_value = _sync_result(gateway, applied=True, grant_count=1)
    output = StringIO()

    call_command("add_global_gateway_administrators", username=["alice"], apply=True, stdout=output)

    reconcile.assert_called_once_with(
        gateway.id,
        apply=True,
        operator=BK_IAM_V4_SYSTEM_ID,
        username="alice",
    )
    assert "summary gateways=1 planned=0 applied=1 unchanged=1 failed=0\n" in output.getvalue()


def test_add_global_gateway_administrators_rejects_too_long_username(settings):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="长度不能超过 64"):
        call_command("add_global_gateway_administrators", username=["a" * 65])


def test_add_global_gateway_administrators_accepts_comma_separated_usernames(settings, mocker):
    _enable_iam(settings)
    gateway = G(Gateway, tenant_mode="global", tenant_id="")
    add_administrators = mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.add_gateway_administrators",
        return_value=["alice", "bob", "charlie"],
    )
    mocker.patch(
        "apigateway.apps.rbac.management.commands.add_global_gateway_administrators.GatewayIAMAuthorizationSynchronizer"
    )

    call_command(
        "add_global_gateway_administrators",
        "--username",
        "alice, bob",
        "--username",
        "charlie,alice",
        "--apply",
    )

    add_administrators.assert_called_once_with(gateway, ["alice", "bob", "charlie"], "admin")


def test_add_global_gateway_administrators_rejects_empty_comma_separated_username(settings):
    _enable_iam(settings)

    with pytest.raises(CommandError, match="--username 不能为空"):
        call_command("add_global_gateway_administrators", username=["alice,,bob"])
