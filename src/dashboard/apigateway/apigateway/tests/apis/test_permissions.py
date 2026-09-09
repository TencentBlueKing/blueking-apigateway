from types import SimpleNamespace
from unittest import mock

import pytest
from django.core.exceptions import ImproperlyConfigured

from apigateway.apis.permissions import GatewayActionPermission
from apigateway.apps.rbac.constants import GatewayActionEnum, GatewayRoleEnum
from apigateway.apps.rbac.models import GatewayMember

pytestmark = pytest.mark.django_db


def _view(gateway_id=None, **attributes):
    kwargs = {} if gateway_id is None else {"gateway_id": gateway_id}
    return SimpleNamespace(kwargs=kwargs, **attributes)


@pytest.mark.parametrize(
    "username, action, expected",
    [
        ("admin", GatewayActionEnum.MANAGE_GATEWAY.value, True),
        ("admin", GatewayActionEnum.OPERATE_GATEWAY.value, True),
        ("admin", GatewayActionEnum.APPROVE_GATEWAY_PERMISSION.value, True),
        ("operator", GatewayActionEnum.MANAGE_GATEWAY.value, False),
        ("operator", GatewayActionEnum.OPERATE_GATEWAY.value, True),
        ("operator", GatewayActionEnum.APPROVE_GATEWAY_PERMISSION.value, True),
        ("guest", GatewayActionEnum.OPERATE_GATEWAY.value, False),
    ],
)
def test_gateway_permissions_by_role(mocker, fake_request, fake_gateway, username, action, expected):
    GatewayMember.objects.update_or_create(
        gateway=fake_gateway,
        username="operator",
        defaults={"role": GatewayRoleEnum.OPERATOR.value},
    )
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username=username)

    assert permission.has_permission(fake_request, _view(fake_gateway.id, gateway_action=action)) == expected
    assert fake_request.gateway == fake_gateway
    if expected:
        assert fake_request.gateway_member.username == username


def test_gateway_permission_defaults_to_manage(mocker, fake_request, fake_gateway):
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username="operator")
    GatewayMember.objects.create(
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    assert not permission.has_permission(fake_request, _view(fake_gateway.id))


def test_gateway_permission_action_map(mocker, fake_request, fake_gateway):
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username="operator")
    GatewayMember.objects.create(
        gateway=fake_gateway,
        username="operator",
        role=GatewayRoleEnum.OPERATOR.value,
    )

    view = _view(
        fake_gateway.id,
        gateway_action=GatewayActionEnum.MANAGE_GATEWAY.value,
        gateway_action_map={"GET": GatewayActionEnum.OPERATE_GATEWAY.value},
    )

    assert permission.has_permission(fake_request, view)


def test_gateway_permission_rejects_invalid_action(mocker, fake_request, fake_gateway):
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username="admin")

    with pytest.raises(ImproperlyConfigured):
        permission.has_permission(fake_request, _view(fake_gateway.id, gateway_action="invalid"))


def test_gateway_permission_without_gateway_id(fake_request):
    permission = GatewayActionPermission()
    assert permission.has_permission(fake_request, _view())
    assert fake_request.gateway_member is None


def test_gateway_permission_exempt_skips_member_query(mocker, fake_request, fake_gateway):
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    get_member = mocker.patch.object(GatewayMember.objects, "get_gateway_member")

    assert permission.has_permission(fake_request, _view(fake_gateway.id, gateway_permission_exempt=True))
    get_member.assert_not_called()
    assert fake_request.gateway_member is None


def test_superuser_does_not_bypass_gateway_membership(mocker, fake_request, fake_gateway):
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username="guest", is_superuser=True)

    assert not permission.has_permission(
        fake_request,
        _view(fake_gateway.id, gateway_action=GatewayActionEnum.OPERATE_GATEWAY.value),
    )


def test_gateway_permission_rejects_invalid_member_role(mocker, fake_request, fake_gateway, caplog):
    permission = GatewayActionPermission()
    mocker.patch.object(permission, "get_gateway_object", return_value=fake_gateway)
    fake_request.user = mock.MagicMock(username="invalid-role")
    GatewayMember.objects.create(
        gateway=fake_gateway,
        username="invalid-role",
        role="invalid",
    )

    with caplog.at_level("WARNING"):
        assert not permission.has_permission(
            fake_request,
            _view(fake_gateway.id, gateway_action=GatewayActionEnum.OPERATE_GATEWAY.value),
        )
    assert "unknown gateway member role" in caplog.text
