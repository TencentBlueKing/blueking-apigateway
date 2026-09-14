import pytest
from django.db import IntegrityError, transaction
from django.db.models import BigAutoField
from django_dynamic_fixture import G

from apigateway.apps.rbac.constants import GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember

pytestmark = pytest.mark.django_db


class TestGatewayMember:
    def test_model_contract(self):
        id_field = GatewayMember._meta.get_field("id")
        username_field = GatewayMember._meta.get_field("username")
        expires_field = GatewayMember._meta.get_field("expires")
        role_field = GatewayMember._meta.get_field("role")

        assert isinstance(id_field, BigAutoField)
        assert username_field.db_index is True
        assert expires_field.null is True
        assert expires_field.blank is True
        assert [value for value, _ in role_field.choices] == GatewayRoleEnum.get_values()
        assert ("gateway", "username") in GatewayMember._meta.unique_together

    def test_gateway_and_username_are_unique(self, fake_gateway):
        GatewayMember.objects.create(
            gateway=fake_gateway,
            username="alice",
            role=GatewayRoleEnum.ADMINISTRATOR.value,
        )

        with pytest.raises(IntegrityError), transaction.atomic():
            GatewayMember.objects.create(
                gateway=fake_gateway,
                username="alice",
                role=GatewayRoleEnum.OPERATOR.value,
            )

    def test_member_is_deleted_with_gateway(self, fake_gateway):
        member = G(
            GatewayMember,
            gateway=fake_gateway,
            username="alice",
            role=GatewayRoleEnum.ADMINISTRATOR.value,
        )

        fake_gateway.delete()

        assert not GatewayMember.objects.filter(id=member.id).exists()
