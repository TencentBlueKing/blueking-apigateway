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
"""Cover missing-user tolerance for reconciliation and automation."""

from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.utils import timezone
from django_dynamic_fixture import G

from apigateway.apps.rbac.iam_context import GatewayIAMSyncContext
from apigateway.apps.rbac.models import GatewayMember
from apigateway.apps.rbac.tasks import _renew_gateway_member_iam_authorizations
from apigateway.biz.gateway import GatewayHandler, GatewayMemberInput, add_gateway_members
from apigateway.biz.iam import (
    GatewayIAMAuthorizationSynchronizer,
    build_gateway_authorization,
    grant_gateway_authorizations,
)
from apigateway.common.error_codes import APIError
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


@pytest.fixture
def missing_iam(settings, mocker):
    settings.BK_IAM_V4_ENABLED = True
    settings.ENABLE_MULTI_TENANT_MODE = False
    settings.BK_API_URL_TMPL = "https://{api_name}.example.com"

    def post(**kwargs):
        missing = [item["subject"]["id"] for item in kwargs["data"] if item["subject"]["id"] == "missing"]
        if not missing:
            return True, {"data": None}
        return False, {
            "error": "some subject not found",
            "status_code": 400,
            "response_data": {
                "error": {"code": "INVALID_REQUEST", "data": {"missing_users": missing}},
            },
        }

    mocker.patch("apigateway.components.bkiam.http_delete", return_value=(True, {"data": None}))
    mocker.patch("apigateway.biz.iam.authorization.iter_authorization_subjects", return_value=[])
    return mocker.patch("apigateway.components.bkiam.http_post", side_effect=post)


def test_member_write_rolls_back_for_missing_iam_user(fake_gateway, missing_iam):
    with pytest.raises(APIError, match="some subject not found"):
        add_gateway_members(fake_gateway, [GatewayMemberInput(username="missing", role="operator")], "admin")
    assert not GatewayMember.objects.filter(gateway=fake_gateway, username="missing").exists()


def test_strict_partial_missing_warning_keeps_gateway_context(fake_gateway, missing_iam, caplog):
    authorizations = [
        build_gateway_authorization(username, "administrator", fake_gateway.id, None)
        for username in ["missing", "alice"]
    ]

    grant_gateway_authorizations(fake_gateway, authorizations, "admin")

    assert missing_iam.call_count == 2
    assert f"gateway_id={fake_gateway.id} gateway_name={fake_gateway.name} missing_users=['missing']" in caplog.text


@pytest.mark.parametrize("with_valid_member", [False, True])
def test_renewal_skips_missing_iam_users(fake_gateway, missing_iam, with_valid_member, caplog):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()
    now = timezone.now()
    member = G(GatewayMember, gateway=fake_gateway, username="missing", role="operator", expires=now)
    if with_valid_member:
        G(GatewayMember, gateway=fake_gateway, username="alice", role="operator", expires=now)
    renewed_expires = now + timedelta(days=365)

    failed = _renew_gateway_member_iam_authorizations(fake_gateway.id, now + timedelta(days=30), renewed_expires)

    member.refresh_from_db()
    assert failed == 0
    assert member.expires == renewed_expires
    assert not GatewayMember.objects.filter(gateway=fake_gateway).exclude(expires=renewed_expires).exists()
    assert missing_iam.call_count == 1 + int(with_valid_member)
    assert "missing_users=['missing']" in caplog.text


@pytest.mark.parametrize("view_name", ["openapi.gateway.sync", "openapi.v2.sync.gateway.sync"])
@pytest.mark.parametrize("create", [False, True])
@pytest.mark.parametrize("with_valid_member", [False, True])
def test_automation_sync_skips_missing_iam_users(
    mocker, request_view, fake_gateway, default_data_plane, missing_iam, view_name, create, with_valid_member, caplog
):
    mocker.patch(
        "apigateway.apis.open.permissions.OpenAPIGatewayRelatedAppPermission.has_permission", return_value=True
    )
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission", return_value=True
    )
    fake_gateway.name = "existing-automation-sync"
    fake_gateway.save(update_fields=["name"])
    GatewayHandler.save_auth_config(fake_gateway.id, user_auth_type="default")
    gateway_name = "automation-sync" if create else fake_gateway.name
    maintainers = ["missing", "alice"] if with_valid_member else ["missing"]

    response = request_view(
        method="POST",
        view_name=view_name,
        path_params={"gateway_name": gateway_name},
        gateway=None if create else fake_gateway,
        app=mocker.Mock(app_code="test-app"),
        data={"description": "synced", "maintainers": maintainers},
    )

    assert response.status_code == 200, response.json()
    gateway = Gateway.objects.get(name=gateway_name)
    assert gateway.description == "synced"
    assert set(maintainers) <= set(GatewayMember.objects.list_gateway_administrators(gateway.id))
    assert missing_iam.call_count == 1 + int(with_valid_member)
    assert f"gateway_id={gateway.id} gateway_name={gateway.name}" in caplog.text
    assert "missing_users=['missing']" in caplog.text


@pytest.mark.parametrize("view_name", ["openapi.gateway.sync", "openapi.v2.sync.gateway.sync"])
@pytest.mark.parametrize("create", [False, True])
def test_automation_sync_rolls_back_for_other_iam_errors(
    mocker, request_view, fake_gateway, default_data_plane, missing_iam, view_name, create
):
    mocker.patch(
        "apigateway.apis.open.permissions.OpenAPIGatewayRelatedAppPermission.has_permission", return_value=True
    )
    mocker.patch(
        "apigateway.apis.v2.permissions.OpenAPIV2GatewayRelatedAppPermission.has_permission", return_value=True
    )
    fake_gateway.name = "existing-automation-sync"
    fake_gateway.save(update_fields=["name"])
    original_description = fake_gateway.description
    missing_iam.side_effect = lambda **kwargs: (False, {"status_code": 503, "error": "IAM unavailable"})
    gateway_name = "automation-sync" if create else fake_gateway.name

    response = request_view(
        method="POST",
        view_name=view_name,
        path_params={"gateway_name": gateway_name},
        gateway=None if create else fake_gateway,
        app=mocker.Mock(app_code="test-app"),
        data={"description": "synced", "maintainers": ["alice"]},
    )

    assert response.status_code == 500, response.json()
    if create:
        assert not Gateway.objects.filter(name=gateway_name).exists()
    else:
        fake_gateway.refresh_from_db()
        assert fake_gateway.description == original_description
        assert not GatewayMember.objects.filter(gateway=fake_gateway, username="alice").exists()


@pytest.mark.parametrize(
    "usernames,retry_fails", [(["missing"], False), (["missing", "alice"], False), (["missing", "alice"], True)]
)
def test_initial_sync_skips_missing_and_completes(fake_gateway, missing_iam, usernames, retry_fails, caplog):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()
    for username in usernames:
        G(GatewayMember, gateway=fake_gateway, username=username, role="administrator")
    if retry_fails:
        initial_post = missing_iam.side_effect

        def post(**kwargs):
            if [item["subject"]["id"] for item in kwargs["data"]] == ["alice"]:
                return False, {"error": "IAM unavailable", "status_code": 500}
            return initial_post(**kwargs)

        missing_iam.side_effect = post
    output = StringIO()

    call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, gateway_delay=0, stdout=output)

    assert GatewayIAMSyncContext().is_initial_sync_completed()
    assert "skipped_missing=1" in output.getvalue()
    assert "grants_planned=" in output.getvalue()
    assert "status=incomplete" not in output.getvalue()
    assert f"gateway_id={fake_gateway.id} gateway_name={fake_gateway.name}" in caplog.text
    assert "missing_users=['missing']" in caplog.text
    assert missing_iam.call_count == len(usernames)
    if retry_fails:
        assert "retry bkiam authorizations failed" in caplog.text
    call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, stdout=output)
    assert missing_iam.call_count == len(usernames)
    assert "reason=initial-sync-already-completed" in output.getvalue()


def test_configured_exclusions_are_removed_from_both_sides_of_plan(
    settings, mocker, fake_gateway, missing_iam, caplog
):
    settings.ENABLE_MULTI_TENANT_MODE = True
    settings.BK_IAM_V4_EXCLUDED_USERNAMES = frozenset({"admin"})
    mocker.patch(
        "apigateway.biz.iam.authorization.iter_authorization_subjects",
        return_value=[
            {
                "id": "admin",
                "expired_at": int((timezone.now() + timedelta(days=100)).timestamp()),
            }
        ],
    )

    plan = GatewayIAMAuthorizationSynchronizer().reconcile_gateway(fake_gateway.id, apply=False, operator="admin")

    assert plan.grants == ()
    assert plan.revokes == ()
    assert plan.excluded_members == 1
    output = StringIO()
    call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, stdout=output)
    assert GatewayIAMSyncContext().is_initial_sync_completed()
    assert "excluded_members=1" in output.getvalue()
    assert "completed-with-warnings" not in output.getvalue()
    assert "skip excluded gateway IAM authorizations" not in caplog.text
    missing_iam.assert_not_called()


@pytest.mark.parametrize("with_valid_member", [False, True])
def test_missing_user_does_not_fail_or_stop_other_gateways(fake_gateway, missing_iam, with_valid_member):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()
    G(GatewayMember, gateway=fake_gateway, username="missing", role="administrator")
    if with_valid_member:
        G(GatewayMember, gateway=fake_gateway, username="alice", role="operator")
    other_gateway = G(Gateway)
    G(GatewayMember, gateway=other_gateway, username="bob", role="administrator")
    output = StringIO()

    call_command("sync_gateway_rbac_auth_to_iam", initial=True, all=True, apply=True, gateway_delay=0, stdout=output)

    lines = output.getvalue().splitlines()
    gateway_lines = [line for line in lines if "event=iam-rbac-sync-gateway" in line]
    assert len(gateway_lines) == 2
    assert f"gateway_id={fake_gateway.id}" in gateway_lines[0]
    assert "skipped_missing=1" in gateway_lines[0]
    assert f"gateway_id={other_gateway.id}" in gateway_lines[1]
    summary = next(line for line in lines if "event=iam-rbac-sync-summary" in line)
    assert "gateways_total=2 gateways_succeeded=2 gateways_failed=0" in summary
    assert "skipped_missing=1" in summary
    assert missing_iam.call_count == 2 + int(with_valid_member)
    assert [item["subject"]["id"] for item in missing_iam.call_args.kwargs["data"]] == ["bob"]
    assert GatewayIAMSyncContext().is_initial_sync_completed()
