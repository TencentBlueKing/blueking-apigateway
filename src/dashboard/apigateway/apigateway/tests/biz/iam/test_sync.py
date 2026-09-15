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

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.iam.sync import GatewayIAMAuthorizationSynchronizer
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


def _expires(timestamp: int) -> datetime:
    return datetime.fromtimestamp(timestamp, tz=UTC)


def _iam_result(username: str, expired_at: int) -> dict:
    return {"id": username, "expired_at": expired_at}


def _mock_iam(mocker, authorizations_by_role):
    def list_authorizations(payload):
        results = authorizations_by_role.get(payload["role_id"], [])
        return {"count": len(results), "results": results}

    return mocker.patch(
        "apigateway.biz.iam.sync.list_authorization_subject",
        side_effect=list_authorizations,
    )


def test_reconcile_plan_adds_fixes_revokes_and_refreshes_expiry(fake_gateway, mocker):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()
    GatewayMember.objects.bulk_create(
        [
            GatewayMember(
                gateway=fake_gateway,
                username="alice",
                role=GatewayRoleEnum.ADMINISTRATOR.value,
                expires=_expires(1_900_000_000),
            ),
            GatewayMember(
                gateway=fake_gateway,
                username="bob",
                role=GatewayRoleEnum.OPERATOR.value,
                expires=_expires(1_900_000_100),
            ),
            GatewayMember(
                gateway=fake_gateway,
                username="refresh",
                role=GatewayRoleEnum.OPERATOR.value,
                expires=_expires(1_900_000_200),
            ),
        ]
    )
    _mock_iam(
        mocker,
        {
            GatewayRoleEnum.ADMINISTRATOR.value: [
                _iam_result("bob", 1_900_000_100),
                _iam_result("extra", 1_900_000_300),
            ],
            GatewayRoleEnum.OPERATOR.value: [
                _iam_result("refresh", 1_800_000_000),
            ],
        },
    )

    result = GatewayIAMAuthorizationSynchronizer().reconcile_gateway(
        fake_gateway.id,
        apply=False,
        operator="admin",
    )

    assert [(item.username, item.role, item.reason) for item in result.grants] == [
        ("alice", "administrator", "missing"),
        ("bob", "operator", "role-mismatch"),
        ("refresh", "operator", "expiry-refresh"),
    ]
    assert [(item.username, item.role, item.reason) for item in result.revokes] == [
        ("bob", "administrator", "role-mismatch"),
        ("extra", "administrator", "extra"),
    ]
    assert result.unchanged == 0
    assert result.applied is False


def test_reconcile_reads_all_pages_for_every_known_role(fake_gateway, mocker):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()

    pages = {
        ("administrator", 1): [_iam_result("a", 1_900_000_000)],
        ("administrator", 2): [_iam_result("b", 1_900_000_000)],
        ("operator", 1): [_iam_result("c", 1_900_000_000)],
        ("operator", 2): [_iam_result("d", 1_900_000_000)],
    }

    def list_authorizations(payload):
        return {
            "count": 2,
            "results": pages[(payload["role_id"], payload["page"])],
        }

    list_api = mocker.patch(
        "apigateway.biz.iam.sync.list_authorization_subject",
        side_effect=list_authorizations,
    )

    result = GatewayIAMAuthorizationSynchronizer(page_size=1).reconcile_gateway(
        fake_gateway.id,
        apply=False,
        operator="admin",
    )

    assert [item.username for item in result.revokes] == ["a", "b", "c", "d"]
    assert [
        (call.args[0]["role_id"], call.args[0]["page"], call.args[0]["page_size"]) for call in list_api.call_args_list
    ] == [
        ("administrator", 1, 1),
        ("administrator", 2, 1),
        ("operator", 1, 1),
        ("operator", 2, 1),
    ]


def test_reconcile_dry_run_does_not_write_iam(fake_gateway, mocker):
    _mock_iam(mocker, {})
    add = mocker.patch("apigateway.biz.iam.sync.add_authorization")
    revoke = mocker.patch("apigateway.biz.iam.sync.revoke_authorization")

    result = GatewayIAMAuthorizationSynchronizer().reconcile_gateway(
        fake_gateway.id,
        apply=False,
        operator="admin",
    )

    assert result.change_count
    add.assert_not_called()
    revoke.assert_not_called()


def test_reconcile_apply_locks_gateway_and_batches_changes(fake_gateway, mocker):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()
    GatewayMember.objects.bulk_create(
        [
            GatewayMember(
                gateway=fake_gateway,
                username=f"user-{index:02d}",
                role=GatewayRoleEnum.OPERATOR.value,
                expires=_expires(1_900_000_000 + index),
            )
            for index in range(25)
        ]
    )
    _mock_iam(mocker, {})
    select_for_update = mocker.patch.object(
        Gateway.objects,
        "select_for_update",
        wraps=Gateway.objects.select_for_update,
    )
    add = mocker.patch("apigateway.biz.iam.sync.add_authorization")

    result = GatewayIAMAuthorizationSynchronizer().reconcile_gateway(
        fake_gateway.id,
        apply=True,
        operator="admin",
    )

    select_for_update.assert_called_once_with()
    assert [len(call.args[0]) for call in add.call_args_list] == [20, 5]
    assert all(call.args[1] == "admin" for call in add.call_args_list)
    assert result.applied is True


def test_reconcile_apply_failure_leaves_local_member_unchanged(fake_gateway, mocker):
    member = GatewayMember.objects.get(gateway=fake_gateway)
    member.role = GatewayRoleEnum.ADMINISTRATOR.value
    member.expires = _expires(1_900_000_000)
    member.save(update_fields=["role", "expires"])
    _mock_iam(
        mocker,
        {
            GatewayRoleEnum.OPERATOR.value: [
                _iam_result(member.username, 1_900_000_000),
            ]
        },
    )
    calls = []
    mocker.patch(
        "apigateway.biz.iam.sync.revoke_authorization",
        side_effect=lambda payloads, operator: calls.append("revoke"),
    )
    mocker.patch(
        "apigateway.biz.iam.sync.add_authorization",
        side_effect=RuntimeError("grant failed"),
    )

    with pytest.raises(RuntimeError, match="grant failed"):
        GatewayIAMAuthorizationSynchronizer().reconcile_gateway(
            fake_gateway.id,
            apply=True,
            operator="admin",
        )

    member.refresh_from_db()
    assert calls == ["revoke"]
    assert member.role == GatewayRoleEnum.ADMINISTRATOR.value
    assert member.expires == _expires(1_900_000_000)


def test_reconcile_username_filters_operations_after_full_iam_query(fake_gateway, mocker):
    GatewayMember.objects.filter(gateway=fake_gateway).delete()
    list_api = _mock_iam(
        mocker,
        {
            "administrator": [
                _iam_result("target", 1_900_000_000),
                _iam_result("other", 1_900_000_000),
            ]
        },
    )

    result = GatewayIAMAuthorizationSynchronizer().reconcile_gateway(
        fake_gateway.id,
        apply=False,
        operator="admin",
        username="target",
    )

    assert [item.username for item in result.revokes] == ["target"]
    assert [call.args[0]["role_id"] for call in list_api.call_args_list] == [
        "administrator",
        "operator",
    ]


def test_reconcile_ignores_small_expiry_difference(fake_gateway, mocker):
    member = GatewayMember.objects.get(gateway=fake_gateway)
    member.expires = _expires(1_900_000_000)
    member.save(update_fields=["expires"])
    _mock_iam(
        mocker,
        {
            member.role: [_iam_result(member.username, 1_900_000_030)],
        },
    )

    result = GatewayIAMAuthorizationSynchronizer(expiry_tolerance=timedelta(minutes=1)).reconcile_gateway(
        fake_gateway.id, apply=False, operator="admin"
    )

    assert result.grants == ()
    assert result.revokes == ()
    assert result.unchanged == 1
