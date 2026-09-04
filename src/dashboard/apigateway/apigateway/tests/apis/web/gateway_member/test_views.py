import pytest
from ddf import G

from apigateway.apps.audit.models import AuditEventLog
from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


class TestGatewayMemberListCreateApi:
    def test_list_only_returns_current_gateway_members(self, request_view, fake_gateway):
        G(
            GatewayMember,
            gateway=fake_gateway,
            username="operator",
            role=GatewayRoleEnum.OPERATOR.value,
        )
        another_gateway = G(Gateway)
        G(
            GatewayMember,
            gateway=another_gateway,
            username="other",
            role=GatewayRoleEnum.OPERATOR.value,
        )

        response = request_view(
            method="GET",
            view_name="gateway_member.list_create",
            path_params={"gateway_id": fake_gateway.id},
        )
        result = response.json()

        assert response.status_code == 200
        assert [member["username"] for member in result["data"]] == ["admin", "operator"]
        assert all("expires" not in member for member in result["data"])

    def test_create_returns_created_and_skipped_members(self, request_view, fake_gateway):
        response = request_view(
            method="POST",
            view_name="gateway_member.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=[
                {"username": "operator", "role": GatewayRoleEnum.OPERATOR.value},
                {"username": "admin", "role": GatewayRoleEnum.OPERATOR.value},
            ],
            format="json",
        )
        result = response.json()

        assert response.status_code == 201
        assert [member["username"] for member in result["data"]["created"]] == ["operator"]
        assert [member["username"] for member in result["data"]["skipped"]] == ["admin"]
        assert "expires" not in result["data"]["created"][0]
        assert GatewayMember.objects.get(gateway=fake_gateway, username="admin").role == (
            GatewayRoleEnum.ADMINISTRATOR.value
        )
        assert AuditEventLog.objects.filter(comment="添加网关成员").count() == 1

    def test_create_rejects_duplicate_usernames(self, request_view, fake_gateway):
        response = request_view(
            method="POST",
            view_name="gateway_member.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=[
                {"username": "operator", "role": GatewayRoleEnum.OPERATOR.value},
                {"username": "operator", "role": GatewayRoleEnum.ADMINISTRATOR.value},
            ],
            format="json",
        )

        assert response.status_code == 400
        assert not GatewayMember.objects.filter(gateway=fake_gateway, username="operator").exists()

    def test_create_rejects_invalid_role(self, request_view, fake_gateway):
        response = request_view(
            method="POST",
            view_name="gateway_member.list_create",
            path_params={"gateway_id": fake_gateway.id},
            data=[{"username": "operator", "role": "invalid"}],
            format="json",
        )

        assert response.status_code == 400

    def test_operator_has_no_access(self, request_view, fake_admin_user, fake_gateway):
        G(
            GatewayMember,
            gateway=fake_gateway,
            username="operator",
            role=GatewayRoleEnum.OPERATOR.value,
        )
        fake_admin_user.username = "operator"

        response = request_view(
            method="GET",
            view_name="gateway_member.list_create",
            path_params={"gateway_id": fake_gateway.id},
            user=fake_admin_user,
        )

        assert response.status_code == 403


class TestGatewayMemberUpdateDestroyApi:
    def test_update_role(self, request_view, fake_gateway):
        GatewayMember.objects.add_gateway_administrators(fake_gateway.id, ["another-admin"], "admin")
        member = GatewayMember.objects.get(gateway=fake_gateway, username="admin")

        response = request_view(
            method="PATCH",
            view_name="gateway_member.update_destroy",
            path_params={"gateway_id": fake_gateway.id, "member_id": member.id},
            data={"role": GatewayRoleEnum.OPERATOR.value},
            format="json",
        )
        result = response.json()

        assert response.status_code == 200
        assert result["data"]["role"] == GatewayRoleEnum.OPERATOR.value
        assert "expires" not in result["data"]
        assert AuditEventLog.objects.filter(comment="变更网关成员角色").count() == 1

    def test_update_same_role_does_not_record_audit(self, request_view, fake_gateway):
        member = GatewayMember.objects.get(gateway=fake_gateway, username="admin")

        response = request_view(
            method="PATCH",
            view_name="gateway_member.update_destroy",
            path_params={"gateway_id": fake_gateway.id, "member_id": member.id},
            data={"role": GatewayRoleEnum.ADMINISTRATOR.value},
            format="json",
        )

        assert response.status_code == 200
        assert not AuditEventLog.objects.filter(comment="变更网关成员角色").exists()

    def test_update_rejects_last_administrator_demotion(self, request_view, fake_gateway):
        member = GatewayMember.objects.get(gateway=fake_gateway, username="admin")

        response = request_view(
            method="PATCH",
            view_name="gateway_member.update_destroy",
            path_params={"gateway_id": fake_gateway.id, "member_id": member.id},
            data={"role": GatewayRoleEnum.OPERATOR.value},
            format="json",
        )

        assert response.status_code == 400
        member.refresh_from_db()
        assert member.role == GatewayRoleEnum.ADMINISTRATOR.value

    def test_delete_member(self, request_view, fake_gateway):
        member = G(
            GatewayMember,
            gateway=fake_gateway,
            username="operator",
            role=GatewayRoleEnum.OPERATOR.value,
        )

        response = request_view(
            method="DELETE",
            view_name="gateway_member.update_destroy",
            path_params={"gateway_id": fake_gateway.id, "member_id": member.id},
        )

        assert response.status_code == 204
        assert not GatewayMember.objects.filter(id=member.id).exists()
        assert AuditEventLog.objects.filter(comment="移除网关成员").count() == 1

    def test_delete_rejects_last_administrator(self, request_view, fake_gateway):
        member = GatewayMember.objects.get(gateway=fake_gateway, username="admin")

        response = request_view(
            method="DELETE",
            view_name="gateway_member.update_destroy",
            path_params={"gateway_id": fake_gateway.id, "member_id": member.id},
        )

        assert response.status_code == 400
        assert GatewayMember.objects.filter(id=member.id).exists()
