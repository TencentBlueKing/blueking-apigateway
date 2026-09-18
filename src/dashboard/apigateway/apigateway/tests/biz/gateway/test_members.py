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
import pytest
from django.db import IntegrityError
from pydantic import ValidationError

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.gateway import (
    GatewayMemberInput,
    add_gateway_administrators,
    add_gateway_members,
    build_gateway_doc_maintainers,
    delete_gateway_member,
    replace_gateway_administrators,
    update_gateway_member_role,
)
from apigateway.biz.gateway import members as gateway_members
from apigateway.common.error_codes import APIError
from apigateway.core.constants import GatewayKindEnum

pytestmark = pytest.mark.django_db


def test_replace_gateway_administrators(fake_gateway):
    assert replace_gateway_administrators(fake_gateway, ["new-admin"], "operator-user") == ["new-admin"]

    assert GatewayMember.objects.list_gateway_administrators(fake_gateway.id) == ["new-admin"]


def test_add_gateway_administrators(fake_gateway):
    assert add_gateway_administrators(fake_gateway, ["new-admin"], "operator-user") == ["admin", "new-admin"]

    assert GatewayMember.objects.list_gateway_administrators(fake_gateway.id) == ["admin", "new-admin"]


def test_build_gateway_doc_maintainers_falls_back_to_administrators(fake_gateway):
    assert build_gateway_doc_maintainers(fake_gateway, ["admin"]) == {
        "type": "user",
        "contacts": ["admin"],
        "service_account": {
            "name": "",
            "link": "",
        },
    }


def test_build_gateway_doc_maintainers_preserves_explicit_config(fake_gateway):
    doc_maintainers = {
        "type": "service_account",
        "contacts": [],
        "service_account": {
            "name": "API Gateway",
            "link": "https://example.com",
        },
    }
    fake_gateway.doc_maintainers = doc_maintainers

    assert build_gateway_doc_maintainers(fake_gateway, ["admin"]) == doc_maintainers


def test_replace_gateway_administrators_rolls_back_on_member_write_failure(fake_gateway, mocker):
    mocker.patch(
        "apigateway.apps.rbac.managers.GatewayMemberManager.bulk_create",
        side_effect=IntegrityError("failed"),
    )

    with pytest.raises(IntegrityError):
        replace_gateway_administrators(fake_gateway, ["new-admin"], "operator-user")

    assert GatewayMember.objects.list_gateway_administrators(fake_gateway.id) == ["admin"]


def test_add_gateway_members_syncs_programmable_gateway_administrators(fake_gateway, mocker):
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    update_app_maintainers = mocker.patch("apigateway.biz.gateway.members.update_app_maintainers")

    result = add_gateway_members(
        fake_gateway,
        [GatewayMemberInput(username="new-admin", role=GatewayRoleEnum.ADMINISTRATOR)],
        "operator-user",
    )

    assert [member.username for member in result.created] == ["new-admin"]
    update_app_maintainers.assert_called_once_with(fake_gateway.name, ["admin", "new-admin"])


def test_add_gateway_members_rolls_back_when_paas_sync_fails(fake_gateway, mocker):
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    mocker.patch(
        "apigateway.biz.gateway.members.update_app_maintainers",
        side_effect=RuntimeError("failed"),
    )

    with pytest.raises(RuntimeError, match="failed"):
        add_gateway_members(
            fake_gateway,
            [GatewayMemberInput(username="new-admin", role=GatewayRoleEnum.ADMINISTRATOR)],
            "operator-user",
        )

    assert not GatewayMember.objects.filter(gateway=fake_gateway, username="new-admin").exists()


def test_add_gateway_members_does_not_sync_operator_only_change(fake_gateway, mocker):
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    update_app_maintainers = mocker.patch("apigateway.biz.gateway.members.update_app_maintainers")

    add_gateway_members(
        fake_gateway,
        [GatewayMemberInput(username="operator", role=GatewayRoleEnum.OPERATOR)],
        "operator-user",
    )

    update_app_maintainers.assert_not_called()


def test_add_gateway_members_rejects_duplicate_usernames(fake_gateway):
    with pytest.raises(APIError):
        add_gateway_members(
            fake_gateway,
            [
                GatewayMemberInput(username="operator", role=GatewayRoleEnum.OPERATOR),
                GatewayMemberInput(username="operator", role=GatewayRoleEnum.ADMINISTRATOR),
            ],
            "operator-user",
        )


def test_gateway_member_input_rejects_invalid_role():
    with pytest.raises(ValidationError):
        GatewayMemberInput(username="operator", role="invalid")


def test_update_gateway_member_role_rolls_back_when_paas_sync_fails(fake_gateway, mocker):
    GatewayMember.objects.add_gateway_administrators(fake_gateway.id, ["another-admin"], "operator-user")
    member = GatewayMember.objects.get(gateway=fake_gateway, username="admin")
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    mocker.patch(
        "apigateway.biz.gateway.members.update_app_maintainers",
        side_effect=RuntimeError("failed"),
    )

    with pytest.raises(RuntimeError, match="failed"):
        update_gateway_member_role(
            fake_gateway,
            member.id,
            GatewayRoleEnum.OPERATOR,
            "operator-user",
        )

    member.refresh_from_db()
    assert member.role == GatewayRoleEnum.ADMINISTRATOR.value


def test_delete_gateway_member_rolls_back_when_paas_sync_fails(fake_gateway, mocker):
    GatewayMember.objects.add_gateway_administrators(fake_gateway.id, ["another-admin"], "operator-user")
    member = GatewayMember.objects.get(gateway=fake_gateway, username="admin")
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    mocker.patch(
        "apigateway.biz.gateway.members.update_app_maintainers",
        side_effect=RuntimeError("failed"),
    )

    with pytest.raises(RuntimeError, match="failed"):
        delete_gateway_member(fake_gateway, member.id, "operator-user")

    assert GatewayMember.objects.filter(id=member.id).exists()


def test_member_write_locks_gateway_before_reading_snapshot(fake_gateway, mocker):
    events = []
    original_lock = gateway_members._lock_gateway
    original_snapshot = gateway_members._get_gateway_member_snapshot
    mocker.patch(
        "apigateway.biz.gateway.members._lock_gateway",
        side_effect=lambda gateway: (events.append("lock"), original_lock(gateway))[1],
    )
    mocker.patch(
        "apigateway.biz.gateway.members._get_gateway_member_snapshot",
        side_effect=lambda gateway_id: (events.append("snapshot"), original_snapshot(gateway_id))[1],
    )

    add_gateway_administrators(fake_gateway, ["new-admin"], "operator-user")

    assert events[:2] == ["lock", "snapshot"]


def test_all_member_writes_apply_iam_deltas(settings, fake_gateway, mocker):
    settings.BK_IAM_V4_ENABLED = True
    apply_iam = mocker.patch("apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam")

    replace_gateway_administrators(fake_gateway, ["admin", "second-admin"], "operator-user")
    add_gateway_administrators(fake_gateway, ["third-admin"], "operator-user")
    result = add_gateway_members(
        fake_gateway,
        [GatewayMemberInput(username="operator", role=GatewayRoleEnum.OPERATOR)],
        "operator-user",
    )
    update_gateway_member_role(
        fake_gateway,
        result.created[0].id,
        GatewayRoleEnum.ADMINISTRATOR,
        "operator-user",
    )
    delete_gateway_member(fake_gateway, result.created[0].id, "operator-user")

    assert apply_iam.call_count == 5
    assert all(call.args[0] == fake_gateway.id for call in apply_iam.call_args_list)
    assert all(call.args[3] == "operator-user" for call in apply_iam.call_args_list)


def test_member_write_does_not_call_iam_when_disabled(settings, fake_gateway, mocker):
    settings.BK_IAM_V4_ENABLED = False
    apply_iam = mocker.patch("apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam")

    add_gateway_administrators(fake_gateway, ["new-admin"], "operator-user")

    apply_iam.assert_not_called()


def test_member_write_rolls_back_local_state_when_iam_fails(settings, fake_gateway, mocker):
    settings.BK_IAM_V4_ENABLED = True
    mocker.patch(
        "apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam",
        side_effect=RuntimeError("iam failed"),
    )

    with pytest.raises(RuntimeError, match="iam failed"):
        add_gateway_members(
            fake_gateway,
            [GatewayMemberInput(username="operator", role=GatewayRoleEnum.OPERATOR)],
            "operator-user",
        )

    assert not GatewayMember.objects.filter(gateway=fake_gateway, username="operator").exists()


def test_iam_failure_restores_programmable_gateway_administrators(settings, fake_gateway, mocker):
    settings.BK_IAM_V4_ENABLED = True
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    update_app_maintainers = mocker.patch("apigateway.biz.gateway.members.update_app_maintainers")
    mocker.patch(
        "apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam",
        side_effect=RuntimeError("iam failed"),
    )

    with pytest.raises(RuntimeError, match="iam failed"):
        add_gateway_members(
            fake_gateway,
            [GatewayMemberInput(username="new-admin", role=GatewayRoleEnum.ADMINISTRATOR)],
            "operator-user",
        )

    assert update_app_maintainers.call_args_list == [
        mocker.call(fake_gateway.name, ["admin", "new-admin"]),
        mocker.call(fake_gateway.name, ["admin"]),
    ]
    assert not GatewayMember.objects.filter(gateway=fake_gateway, username="new-admin").exists()


def test_iam_failure_does_not_sync_paas_when_administrator_set_is_unchanged(
    settings,
    fake_gateway,
    mocker,
):
    settings.BK_IAM_V4_ENABLED = True
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    update_app_maintainers = mocker.patch("apigateway.biz.gateway.members.update_app_maintainers")
    mocker.patch(
        "apigateway.biz.gateway.members.apply_gateway_member_snapshots_to_iam",
        side_effect=RuntimeError("iam failed"),
    )

    with pytest.raises(RuntimeError, match="iam failed"):
        add_gateway_members(
            fake_gateway,
            [GatewayMemberInput(username="operator", role=GatewayRoleEnum.OPERATOR)],
            "operator-user",
        )

    update_app_maintainers.assert_not_called()
