import pytest
from django.db import IntegrityError

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.gateway import (
    add_gateway_administrators,
    add_gateway_members,
    build_gateway_doc_maintainers,
    delete_gateway_member,
    replace_gateway_administrators,
    update_gateway_member_role,
)
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
        [("new-admin", GatewayRoleEnum.ADMINISTRATOR.value)],
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
            [("new-admin", GatewayRoleEnum.ADMINISTRATOR.value)],
            "operator-user",
        )

    assert not GatewayMember.objects.filter(gateway=fake_gateway, username="new-admin").exists()


def test_add_gateway_members_does_not_sync_operator_only_change(fake_gateway, mocker):
    fake_gateway.kind = GatewayKindEnum.PROGRAMMABLE.value
    fake_gateway.save(update_fields=["kind"])
    update_app_maintainers = mocker.patch("apigateway.biz.gateway.members.update_app_maintainers")

    add_gateway_members(
        fake_gateway,
        [("operator", GatewayRoleEnum.OPERATOR.value)],
        "operator-user",
    )

    update_app_maintainers.assert_not_called()


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
            GatewayRoleEnum.OPERATOR.value,
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
        delete_gateway_member(fake_gateway, member.id)

    assert GatewayMember.objects.filter(id=member.id).exists()
