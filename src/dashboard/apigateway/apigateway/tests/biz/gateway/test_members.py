import pytest
from django.db import IntegrityError

from apigateway.apps.rbac.models import GatewayMember
from apigateway.biz.gateway import (
    add_gateway_administrators,
    build_gateway_doc_maintainers,
    replace_gateway_administrators,
)

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
