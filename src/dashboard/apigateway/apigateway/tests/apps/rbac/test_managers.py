import pytest
from django_dynamic_fixture import G

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember
from apigateway.core.models import Gateway

pytestmark = pytest.mark.django_db


def test_list_gateway_administrators(fake_gateway):
    G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert GatewayMember.objects.list_gateway_administrators(fake_gateway.id) == ["admin"]


def test_list_gateway_approvers_prefers_operators(fake_gateway):
    G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert GatewayMember.objects.list_gateway_approvers(fake_gateway.id) == ["operator"]


def test_list_gateway_approvers_falls_back_to_administrators(fake_gateway):
    assert GatewayMember.objects.list_gateway_approvers(fake_gateway.id) == ["admin"]


def test_build_gateway_member_maps(fake_gateway):
    G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert GatewayMember.objects.build_gateway_administrators_map([fake_gateway.id]) == {fake_gateway.id: ["admin"]}
    assert GatewayMember.objects.build_gateway_approvers_map([fake_gateway.id]) == {fake_gateway.id: ["operator"]}


def test_gateway_member_maps_use_one_query_for_multiple_gateways(django_assert_num_queries, fake_gateway):
    another_gateway = G(Gateway)
    GatewayMember.objects.create(
        gateway=another_gateway,
        username="another-admin",
        role=GatewayRoleEnum.ADMINISTRATOR.value,
    )
    gateway_ids = [fake_gateway.id, another_gateway.id]

    with django_assert_num_queries(1):
        administrators = GatewayMember.objects.build_gateway_administrators_map(gateway_ids)
    with django_assert_num_queries(1):
        approvers = GatewayMember.objects.build_gateway_approvers_map(gateway_ids)

    assert administrators == {
        fake_gateway.id: ["admin"],
        another_gateway.id: ["another-admin"],
    }
    assert approvers == administrators


def test_is_gateway_administrator(fake_gateway):
    assert GatewayMember.objects.is_gateway_administrator(fake_gateway.id, "admin")
    assert not GatewayMember.objects.is_gateway_administrator(fake_gateway.id, "guest")


def test_has_gateway_approve_permission(fake_gateway):
    G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert GatewayMember.objects.has_gateway_approve_permission(fake_gateway.id, "admin")
    assert GatewayMember.objects.has_gateway_approve_permission(fake_gateway.id, "operator")
    assert not GatewayMember.objects.has_gateway_approve_permission(fake_gateway.id, "guest")


def test_list_gateway_ids_by_username(fake_gateway):
    administrator_gateway_ids = GatewayMember.objects.list_gateway_ids_by_username(
        "admin",
        [GatewayRoleEnum.ADMINISTRATOR.value],
    )
    operator_gateway_ids = GatewayMember.objects.list_gateway_ids_by_username(
        "admin",
        [GatewayRoleEnum.OPERATOR.value],
    )

    assert administrator_gateway_ids == [fake_gateway.id]
    assert operator_gateway_ids == []


def test_list_gateway_ids_by_approver_prefers_operators(fake_gateway):
    G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert GatewayMember.objects.list_gateway_ids_by_approver("admin") == []
    assert GatewayMember.objects.list_gateway_ids_by_approver("operator") == [fake_gateway.id]


def test_list_gateway_ids_by_approver_falls_back_to_administrators(fake_gateway):
    assert GatewayMember.objects.list_gateway_ids_by_approver("admin") == [fake_gateway.id]


def test_replace_gateway_administrators_preserves_operators(fake_gateway):
    operator = G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert GatewayMember.objects.replace_gateway_administrators(fake_gateway.id, ["new-admin"], "operator-user") == [
        "new-admin"
    ]
    operator.refresh_from_db()
    assert operator.role == GatewayRoleEnum.OPERATOR.value


def test_add_gateway_administrators_does_not_remove_existing(fake_gateway):
    assert GatewayMember.objects.add_gateway_administrators(fake_gateway.id, ["new-admin"], "operator-user") == [
        "admin",
        "new-admin",
    ]


def test_replace_gateway_administrators_converts_operator(fake_gateway):
    operator = G(
        GatewayMember,
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    GatewayMember.objects.replace_gateway_administrators(fake_gateway.id, ["operator"], "operator-user")

    operator.refresh_from_db()
    assert operator.role == GatewayRoleEnum.ADMINISTRATOR.value


def test_replace_gateway_administrators_rejects_empty_administrators(fake_gateway):
    with pytest.raises(ValueError):
        GatewayMember.objects.replace_gateway_administrators(fake_gateway.id, [], "operator-user")
