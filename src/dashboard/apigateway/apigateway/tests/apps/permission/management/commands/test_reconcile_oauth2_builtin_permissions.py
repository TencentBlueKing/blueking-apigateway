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

from io import StringIO

import pytest
from ddf import G
from django.core.management import call_command
from django.core.management.base import CommandError

from apigateway.apps.permission.models import AppResourcePermission
from apigateway.controller.tasks.oauth2_builtin import (
    OAuth2BuiltinPermissionResult,
    ReconciliationBlocker,
)

pytestmark = pytest.mark.django_db

COMMAND_NAME = "reconcile_oauth2_builtin_permissions"


@pytest.fixture(autouse=True)
def mock_permission_lock(mocker):
    lock = mocker.patch("apigateway.controller.tasks.oauth2_builtin.redis_lock.Lock").return_value
    lock.acquire.return_value = True
    return lock


def test_gateway_argument_is_required():
    with pytest.raises(CommandError, match="the following arguments are required: --gateway"):
        call_command(COMMAND_NAME)


def test_unknown_gateway_raises_command_error():
    with pytest.raises(CommandError, match="gateway not found: unknown"):
        call_command(COMMAND_NAME, gateway="unknown")


def test_default_is_dry_run_and_apply_is_idempotent(fake_gateway):
    permission = G(
        AppResourcePermission,
        gateway=fake_gateway,
        bk_app_code="public",
        resource_id=100,
    )

    dry_run_output = StringIO()
    call_command(COMMAND_NAME, gateway=fake_gateway.name, stdout=dry_run_output)

    assert AppResourcePermission.objects.filter(id=permission.id).exists()
    assert "extra count=1 rows=public:100" in dry_run_output.getvalue()
    assert "applied=false" in dry_run_output.getvalue()

    apply_output = StringIO()
    call_command(COMMAND_NAME, gateway=fake_gateway.name, apply=True, stdout=apply_output)
    call_command(COMMAND_NAME, gateway=fake_gateway.name, apply=True)

    assert not AppResourcePermission.objects.filter(id=permission.id).exists()
    assert "applied=true" in apply_output.getvalue()


def test_output_is_complete_sorted_and_reports_blockers(fake_gateway, mocker):
    result = OAuth2BuiltinPermissionResult(
        desired=frozenset({("public", 20), ("personal", 10)}),
        missing=frozenset({("public", 20)}),
        extra=frozenset({("personal", 30)}),
        unchanged=frozenset({("personal", 10)}),
        normalized=frozenset({("personal", 10)}),
        deletion_blocked=True,
        blockers=(
            ReconciliationBlocker(
                stage_id=2,
                stage_name="prod",
                data_plane_id=3,
                data_plane_name="default",
                release_history_id=4,
                status="doing",
            ),
        ),
        applied=False,
    )
    reconcile = mocker.patch(
        "apigateway.apps.permission.management.commands."
        "reconcile_oauth2_builtin_permissions.OAuth2BuiltinPermissionReconciler"
    ).return_value.reconcile_gateway
    reconcile.return_value = result
    output = StringIO()

    call_command(COMMAND_NAME, gateway=fake_gateway.name, stdout=output)

    reconcile.assert_called_once_with(fake_gateway, apply=False)
    assert output.getvalue().splitlines() == [
        "gateway={}".format(fake_gateway.name),
        "desired count=2 rows=personal:10,public:20",
        "missing count=1 rows=public:20",
        "extra count=1 rows=personal:30",
        "unchanged count=1 rows=personal:10",
        "normalized count=1 rows=personal:10",
        "applied=false",
        "deletion_blocked=true",
        "blocked stage=prod(2) data_plane=default(3) release_history=4 status=doing",
    ]


def test_apply_flag_is_forwarded(fake_gateway, mocker):
    result = OAuth2BuiltinPermissionResult(
        desired=frozenset(),
        missing=frozenset(),
        extra=frozenset(),
        unchanged=frozenset(),
        normalized=frozenset(),
        deletion_blocked=False,
        blockers=(),
        applied=True,
    )
    reconcile = mocker.patch(
        "apigateway.apps.permission.management.commands."
        "reconcile_oauth2_builtin_permissions.OAuth2BuiltinPermissionReconciler"
    ).return_value.reconcile_gateway
    reconcile.return_value = result

    call_command(COMMAND_NAME, gateway=fake_gateway.name, apply=True)

    reconcile.assert_called_once_with(fake_gateway, apply=True)
