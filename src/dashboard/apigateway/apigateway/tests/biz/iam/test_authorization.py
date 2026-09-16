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

import pytest
from django.utils import timezone

from apigateway.biz.iam.authorization import (
    GatewayMemberAuthorization,
    apply_gateway_member_snapshots_to_iam,
    build_gateway_authorization,
    build_gateway_revoke_authorization,
    get_gateway_iam_system_operator,
)


def test_build_gateway_authorization_uses_default_expiry_for_null():
    now = timezone.now()

    payload = build_gateway_authorization("alice", "operator", 42, None, now=now)

    assert payload == {
        "subject": {"type": "user", "id": "alice"},
        "role_id": "operator",
        "expired_at": int((now + timedelta(days=365)).timestamp()),
        "related_resource_type_id": "gateway",
        "resources": [{"type": "gateway", "id": "42"}],
    }
    assert build_gateway_revoke_authorization("alice", "operator", 42) == {
        "subject": {"type": "user", "id": "alice"},
        "role_id": "operator",
        "related_resource_type_id": "gateway",
        "resources": [{"type": "gateway", "id": "42"}],
    }


def test_apply_gateway_member_snapshots_revokes_before_granting(mocker):
    calls = []
    revoke = mocker.patch(
        "apigateway.biz.iam.authorization.revoke_authorization",
        side_effect=lambda payload, operator: calls.append(("revoke", payload, operator)),
    )
    grant = mocker.patch(
        "apigateway.biz.iam.authorization.add_authorization",
        side_effect=lambda payload, operator: calls.append(("grant", payload, operator)),
    )
    expires = timezone.now() + timedelta(days=100)
    before = {
        "removed": GatewayMemberAuthorization("operator", expires),
        "changed": GatewayMemberAuthorization("operator", expires),
        "unchanged": GatewayMemberAuthorization("administrator", expires),
    }
    after = {
        "changed": GatewayMemberAuthorization("administrator", expires),
        "unchanged": GatewayMemberAuthorization("administrator", expires),
        "added": GatewayMemberAuthorization("operator", expires),
    }

    apply_gateway_member_snapshots_to_iam(7, before, after, "admin")

    assert [call[0] for call in calls] == ["revoke", "grant"]
    assert {(item["subject"]["id"], item["role_id"]) for item in revoke.call_args.args[0]} == {
        ("changed", "operator"),
        ("removed", "operator"),
    }
    assert {(item["subject"]["id"], item["role_id"]) for item in grant.call_args.args[0]} == {
        ("added", "operator"),
        ("changed", "administrator"),
    }


def test_apply_gateway_member_snapshots_chunks_to_twenty(mocker):
    grant = mocker.patch("apigateway.biz.iam.authorization.add_authorization")
    mocker.patch("apigateway.biz.iam.authorization.revoke_authorization")
    expires = timezone.now() + timedelta(days=100)
    after = {f"user-{index:02d}": GatewayMemberAuthorization("operator", expires) for index in range(45)}

    apply_gateway_member_snapshots_to_iam(7, {}, after, "admin")

    assert [len(call.args[0]) for call in grant.call_args_list] == [20, 20, 5]


def test_apply_gateway_member_snapshots_refreshes_changed_expiry_without_revoking(mocker):
    now = timezone.now()
    new_expires = now + timedelta(days=365)
    before = {"alice": GatewayMemberAuthorization("operator", now + timedelta(days=30))}
    after = {"alice": GatewayMemberAuthorization("operator", new_expires)}
    revoke = mocker.patch("apigateway.biz.iam.authorization.revoke_authorization")
    grant = mocker.patch("apigateway.biz.iam.authorization.add_authorization")

    apply_gateway_member_snapshots_to_iam(7, before, after, "admin")

    revoke.assert_not_called()
    assert grant.call_args.args[0][0]["expired_at"] == int(new_expires.timestamp())


def test_apply_gateway_member_snapshots_restores_before_and_reraises(mocker):
    expires = timezone.now() + timedelta(days=100)
    before = {
        "alice": GatewayMemberAuthorization("operator", expires),
        "unchanged": GatewayMemberAuthorization("operator", expires),
    }
    after = {
        "alice": GatewayMemberAuthorization("administrator", expires),
        "unchanged": GatewayMemberAuthorization("operator", expires),
    }
    revoke = mocker.patch("apigateway.biz.iam.authorization.revoke_authorization")
    grant = mocker.patch(
        "apigateway.biz.iam.authorization.add_authorization",
        side_effect=[RuntimeError("grant failed"), None],
    )

    with pytest.raises(RuntimeError, match="grant failed"):
        apply_gateway_member_snapshots_to_iam(7, before, after, "admin")

    assert revoke.call_count == 2
    assert grant.call_count == 2
    assert grant.call_args_list[-1].args[0][0]["role_id"] == "operator"
    assert {item["subject"]["id"] for item in revoke.call_args_list[-1].args[0]} == {"alice"}


def test_apply_gateway_member_snapshots_logs_compensation_failure(mocker, caplog):
    expires = timezone.now() + timedelta(days=100)
    before = {"alice": GatewayMemberAuthorization("operator", expires)}
    after = {"alice": GatewayMemberAuthorization("administrator", expires)}
    mocker.patch(
        "apigateway.biz.iam.authorization.revoke_authorization",
        side_effect=[None, RuntimeError("compensation failed")],
    )
    mocker.patch(
        "apigateway.biz.iam.authorization.add_authorization",
        side_effect=RuntimeError("grant failed"),
    )

    with caplog.at_level("CRITICAL"), pytest.raises(RuntimeError, match="grant failed"):
        apply_gateway_member_snapshots_to_iam(7, before, after, "admin")

    assert "failed to compensate gateway IAM authorizations" in caplog.text


def test_get_gateway_iam_system_operator_uses_first_manager(settings):
    settings.BK_IAM_V4_MANAGERS = ["admin", "maintainer"]

    assert get_gateway_iam_system_operator() == "admin"


def test_get_gateway_iam_system_operator_rejects_empty_managers(settings):
    settings.BK_IAM_V4_MANAGERS = []

    with pytest.raises(ValueError, match="BK_IAM_V4_MANAGERS"):
        get_gateway_iam_system_operator()
